"""
pw_html_radaddaійного Playwright HTML report для pytest-playwright.

Підключення (у conftest.py):
    pytest_plugins = ["pw_html_report"]

Запуск:
    pytest --headed

Звіт з'являється у playwright-report/index.html. Щоб працював перегляд trace:
    python3 -m http.server 9323 --directory playwright-report
    і відкрити http://localhost:9323

Скріншот, відео й trace вмикаються автоматично, якщо ви не вказали власні значення
--screenshot / --video / --tracing. Вимкнути це: --no-pw-report-defaults.
Взагалі не створювати звіт: --no-pw-report.
"""
impoad
import json
import re
import shutil
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

_RESUad
_ORDER = []
_STATE = {"start": None}
ad_trace": ("trace", "application/zip", "zip"),
}

# Службові виклики Playwright, які не потрібно показувати як кроки тесту
_SKIP_API = {
    "browsercontext.close", "browser.close", "page.close", "browser.newcontext",
    "browsercontext.newpage", "browsertype.launch", "tracing.start", "tracing.stop",
    "tracing.startchunk", "tracing.stopchunk", "browser.newpage",
}
_SKIP_CLASSES = {"Tracing", "Artifact", "Browser", "BrowserType", "Playwright", "LocalUtils"}


# -------ad   help="Не створювати звіт")
    group.addoption("--no-pw-report-defaults", action="store_true", default=False,
                    help="Не вмикати автоматично скріншот, відео й trace")


def pytest_configure(config):
    if config.getoption("--no-pw-report") or config.getoption("--no-pw-report-defaults"):
        return
    for opt in ("screenshot", "video", "tracing"):
        # значення "off" це стандартне значення pytest-playwright
        if getattr(config.option, opt, None) == "off":
            setattr(config.option, opt, "on")
dionstart(session):
    _STATE["start"] = time.time()


def pytest_runtest_logreport(report):
    d = _RESULTS.get(report.nodeid)
    if d is None:
        d = {"phases": {}, "props": [], "location": report.location}
        _RESULTS[report.nodeid] = d
        _ORDER.append(report.nodeid)
    d["phases"][report.when] = report
    d["props"].extend(getattr(report, "user_properties", []) or [])


# ----------------------------------------------------------------------------- допоміжне
def _sha1(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha1(data).hexdigest()


def _iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{int((ts % 1) * 1000):03d}Z"


def _pretty_words(name):
    name = name.replace("_", " ")
    name = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)
    return name.strip().capitalize()


def _prettad
    for part in [p.strip() for p in sel.split(" >> ")]:
        m = re.match(r'^internal:role=([\w-]+)(?:\[name="(.*?)"[is]?\])?', part)
        if m:
            out.append(f'get_by_role("{m.group(1)}"' + (f', name="{m.group(2)}"' if m.group(2) else "") + ")")
            continue
        m = re.match(r'^internal:text="(.*?)"[is]?$', part)
        if m:
            out.append(f'get_by_text("{m.group(1)}")')
            continue
        m = re.match(r'^internal:label="(.*?)"[is]?$', part)
        if m:
            out.append(f'get_by_label("{m.group(1)}")')
            continue
        m = re.match(r'^internal:attr=\[placeholder="(.*?)"[is]?\]$', part)
        if m:
            out.append(f'get_by_placeholder("{m.group(1)}")')
            continue
        m = re.match(r'^internal:testid=\[data-testid="(.*?)"[is]?\]$', part)
        if m:
            out.append(f'get_by_test_id("{m.group(1)}")')
            continue
        m = re.match(r"^nth=(-?\d+)$", part)
        if m:
            out.append("first" if m.group(1) == "0" else "last" if m.group(1) == "-1" else f"nth({m.group(1)})")
            continue
        out.append(f'locator("{part}")')
    return ".".join(out)

adms") or {}
    base = ev.get("title") or ev.get("apiName") or f'{ev.get("class", "")}.{ev.get("method", "")}'
    sel = _pretty_selector(p.get("selector", "")) if isinstance(p.get("selector"), str) else ""
    if base.startswith("Expect"):
        return f"{base} {sel}".strip()
    name = base.split(".")[-1]
    key = name.lower().replace("_", "")
    if key == "expect" and p.get("expression"):
        expr = str(p["expression"]).replace(".", "_")
        return f'Expect "{expr}" {sel}'.strip()
    if key == "goto":
        return f'Navigate to "{p.get("url", "")}"'
    if key == "fill":
        return f'Fill "{p.get("value", "")}" {sel}'.strip()
    if key == "type":
        return f'Type "{p.get("text", "")}" {sel}'.strip()
    if key == "press":
        return f'Press "{p.get("key", "")}" {sel}'.strip()
    if key == "dblclick":
        return f"Double click {sel}".strip()
    if key == "selectoption":
        return f"Select option {sel}".strip()
    if key in ("get", "post", "put", "delete", "patch", "head", "fetch") and p.get("url"):
        verb = (p.get("method") or name).upper()
        return f'{verb} "{p["url"]}"'
    return f"{_pretty_words(name)} {sel}".strip()


def _is_user_file(path, root):
    p = path.replace("\\", "/")
    if not p.endswith(".py"):
        return False
    bad = ("site-packages", "dist-packages", "/playwright/", "/_pytest/", "/pluggy/",
           "pytest_playwright", "/.venv/", "/venv/")
    return not any(b in p for b in bad)


def _frame_tuple(fr, files):
    if isinstance(fr, dict):
        return fr.get("file"), fr.get("line"), fr.get("column", 1)
    if isinstance(fr, (list, tuple)) and len(fr) >= 3:
        idx = fr[0]
        f = files[idx] if isinstance(idx, int) and idx < len(files) else idx
        return f, fr[1], fr[2]
    return None, None, None


def _load_locations(stacks, root):
    """Повертає {callId: (file, line, column)} з trace.stacks."""
    locs = {}
    if not isinstance(stacks, dict):
        return locs
    files = stacks.get("files") or []
    call_ids = stacks.get("callIds") or []
    for item in stacks.get("stacks") or []:
        try:
            ref, frames = item[0], item[1]
        except Exception:
            continue
        keys = [str(ref), f"call@{ref}"]
        if isinstance(ref, int) and ref < len(call_ids):
            keys.append(str(call_ids[ref]))
        for fr in frames or []:
            f, line, col = _frame_tuple(fr, files)
            if f and line and _is_user_file(str(f), root):
                for k in keys:
                    locs[k] = (str(f), int(line), int(col or 1))
                break
    return locs


def _snippet(path, line):
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except Exception:
        return None
    lo, hi = max(1, line - 2), min(len(lines), line + 2)
    width = len(str(hi))
    out = []
    for n in range(lo, hi + 1):
        mark = ">" if n == line else " "
        out.append(f"{mark} {str(n).rjust(width)} | {lines[n - 1]}")
    return "\n".join(out)


def _rel(path, root):
    try:
        return str(Path(path).resolve().relative_to(root))
    except Exception:
        return Path(path).name


def _steps_from_trace(trace_path, root):
    """Читає кроки тесту з trace.zip. При будь-якій проблемі повертає порожній список."""
    try:
        events, stacks = [], None
        with zipfile.ZipFile(trace_path) as z:
            names = z.namelist()
            for n in sorted(names):
                if n.endswith(".trace"):
                    for line in z.read(n).decode("utf-8", "replace").splitlines():
                        line = line.strip()
                        if line:
                            try:
                                events.append(json.loads(line))
                            except ValueError:
                                pass
            for n in names:
                if n.endswith(".stacks"):
                    try:
                        stacks = json.loads(z.read(n).decode("utf-8", "replace"))
                    except ValueError:
                        stacks = None
        locs = _load_locations(stacks, root)
        wall = mono = None
        calls, order = {}, []
        for ev in events:
            t = ev.get("type")
            if t == "context-options":
                wall, mono = ev.get("wallTime"), ev.get("monotonicTime")
            elif t == "before" and ev.get("callId"):
                calls[ev["callId"]] = {"ev": ev, "end": None, "error": None}
                order.append(ev["callId"])
            elif t == "after" and ev.get("callId") in calls:
                c = calls[ev["callId"]]
                c["end"] = ev.get("endTime")
                err = ev.get("error")
                if isinstance(err, dict):
                    c["error"] = err.get("message") or "Error"

        def to_epoch_ms(mono_ms):
            if wall is not None and mono is not None and mono_ms is not None:
                return wall + (mono_ms - mono)
            return mono_ms or 0

        nodes = {}
        for cid in order:
            ev = calls[cid]["ev"]
            cls = ev.get("class") or ""
            api = ev.get("apiName") or (f'{cls}.{ev.get("method")}' if ev.get("method") else "")
            if not api and not ev.get("title"):
                continue
            if ev.get("internal") or cls in _SKIP_CLASSES or api.lower() in _SKIP_API:
                continue
            start = to_epoch_ms(ev.get("startTime"))
            end = to_epoch_ms(calls[cid]["end"]) if calls[cid]["end"] is not None else start
            step = {
                "title": _step_title(ev),
                "startTime": _iso(start / 1000.0),
                "duration": max(0, round(end - start)),
                "attachments": [],
                "count": 1,
                "skipped": False,
                "steps": [],
            }
            loc = locs.get(cid) or locs.get(cid.replace("call@", ""))
            if loc:
                step["location"] = {"file": _rel(loc[0], root), "line": loc[1], "column": loc[2]}
                snip = _snippet(loc[0], loc[1])
                if snip:
                    step["snippet"] = snip
            if calls[cid]["error"]:
                step["error"] = calls[cid]["error"]
            nodes[cid] = (step, ev.get("parentId"))
        top = []
        for cid in order:
            if cid not in nodes:
                continue
            step, parent = nodes[cid]
            if parent in nodes:
                nodes[parent][0]["steps"].append(step)
            else:
                top.append(step)
        return top
    except Exception:
        return []


def _resolve(config, p):
    p = Path(p)
    return p if p.is_absolute() else Path(config.invocation_params.dir) / p


# ----------------------------------------------------------------------------- побудова звіту
def _build_report(config, report_dir):
    root = Path(config.rootpath).resolve()
    data_dir = report_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    browsers = config.getoption("--browser", default=None) or []
    project = browsers[0] if browsers else "chromium"
    started = _STATE["start"] or time.time()

    files = {}

    for nodeid in _ORDER:
        d = _RESULTS[nodeid]
        ph = d["phases"]
        setup, call, teardown = ph.get("setup"), ph.get("call"), ph.get("teardown")
        reps = [r for r in (setup, call, teardown) if r is not None]
        if not reps:
            continue
        duration_ms = round(sum(r.duration for r in reps) * 1000)
        start_ts = min((getattr(r, "start", None) or started) for r in reps)

        failed_rep = next((r for r in (setup, call, teardown) if r is not None and r.failed), None)
        skipped_rep = next((r for r in (setup, call) if r is not None and r.skipped), None)
        xfail = skipped_rep is not None and hasattr(skipped_rep, "wasxfail")
        if failed_rep is not None:
            status, outcome = "failed", "unexpected"
        elif skipped_rep is not None and xfail:
            status, outcome = "failed", "expected"
        elif skipped_rep is not None:
            status, outcome = "skipped", "skipped"
        else:
            status, outcome = "passed", "expected"
        ok = outcome in ("expected", "skipped")

        parts = nodeid.split("::")
        file_name = parts[0]
        title = parts[-1]
        path_titles = parts[1:-1]
        file_id = _sha1(file_name)[:20]
        test_id = f"{file_id}-{_sha1(nodeid)[:20]}"
        line = (d["location"][1] + 1) if d["location"] and d["location"][1] is not None else 1
        location = {"file": file_name, "line": line, "column": 1}

        # вкладення
        attachments, trace_src = [], None
        for key, value in d["props"]:
            if key not in _ARTIFACT_TYPES:
                continue
            name, ctype, ext = _ARTIFACT_TYPES[key]
            src = _resolve(config, value)
            if not src.is_file():
                continue
            blob = src.read_bytes()
            target = f"data/{_sha1(blob)}.{ext}"
            (report_dir / target).write_bytes(blob)
            attachments.append({"name": name, "contentType": ctype, "path": target})
            if name == "trace" and trace_src is None:
                trace_src = src
        order_pref = {"screenshot": 0, "video": 1, "trace": 2}
        attachments.sort(key=lambda a: order_pref.get(a["name"], 9))

        steps = _steps_from_trace(trace_src, root) if trace_src else []

        errors = []
        if failed_rep is not None:
            text = getattr(failed_rep, "longreprtext", "") or "Test failed"
            errors.append({"message": text})

        result = {
            "duration": duration_ms,
            "startTime": _iso(start_ts),
            "retry": 0,
            "steps": steps,
            "errors": errors,
            "status": status,
            "annotations": [],
            "attachments": attachments,
            "workerIndex": 0,
        }
        test = {
            "testId": test_id,
            "title": title,
            "projectName": project,
            "location": location,
            "duration": duration_ms,
            "annotations": [],
            "tags": [],
            "outcome": outcome,
            "path": path_titles,
            "results": [result],
            "ok": ok,
        }
        f = files.setdefault(file_id, {"fileId": file_id, "fileName": file_name, "tests": []})
        f["tests"].append(test)

    # report.json і по одному json на файл
    zbuf = io.BytesIO()
    summary_files = []
    all_stats = {"total": 0, "expected": 0, "unexpected": 0, "flaky": 0, "skipped": 0}
    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files.values():
            st = {"total": 0, "expected": 0, "unexpected": 0, "flaky": 0, "skipped": 0}
            summary_tests = []
            for t in f["tests"]:
                st["total"] += 1
                st[t["outcome"]] += 1
                summary_tests.append({
                    **{k: v for k, v in t.items() if k != "results"},
                    "results": [{
                        "attachments": t["results"][0]["attachments"],
                        "startTime": t["results"][0]["startTime"],
                        "workerIndex": 0,
                    }],
                })
            st["ok"] = st["unexpected"] == 0 and st["flaky"] == 0
            for k in all_stats:
                all_stats[k] += st[k]
            z.writestr(f"{f['fileId']}.json", json.dumps(f, ensure_ascii=False))
            summary_files.append({"fileId": f["fileId"], "fileName": f["fileName"],
                                  "tests": summary_tests, "stats": st})
        all_stats["ok"] = all_stats["unexpected"] == 0 and all_stats["flaky"] == 0
        report_json = {
            "metadata": {"actualWorkers": 1},
            "startTime": round(started * 1000),
            "duration": round((time.time() - started) * 1000),
            "files": summary_files,
            "projectNames": [project],
            "stats": all_stats,
            "errors": [],
            "options": {},
            "machines": [],
        }
        z.writestr("report.json", json.dumps(report_json, ensure_ascii=False))
    return zbuf.getvalue(), all_stats


def _app_dir():
    import playwright
    return Path(playwright.__file__).parent / "driver" / "package" / "lib" / "vite"


def _write_index_html(report_dir, zip_bytes):
    app = _app_dir() / "htmlReport"
    html = (app / "index.html").read_text(encoding="utf-8")
    js = (app / "report.js").read_text(encoding="utf-8")
    css = (app / "report.css").read_text(encoding="utf-8")
    html = html.replace('<script type="module" crossorigin src="./report.js"></script>',
                        '<script type="module">' + js + "</script>")
    html = html.replace('<link rel="stylesheet" crossorigin href="./report.css">',
                        "<style type='text/css'>" + css + "</style>")
    b64 = base64.b64encode(zip_bytes).decode("ascii")
    html += f'\n<template id="playwrightReportBase64">data:application/zip;base64,{b64}</template>'
    (report_dir / "index.html").write_text(html, encoding="utf-8")


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    config = session.config
    if config.getoption("--no-pw-report") or hasattr(config, "workerinput"):
        return
    if not _RESULTS:
        return
    report_dir = _resolve(config, config.getoption("--pw-report-dir"))
    # чистимо лише те, що створює сам плагін
    for sub in ("data", "trace"):
        shutil.rmtree(report_dir / sub, ignore_errors=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    try:
        zip_bytes, stats = _build_report(config, report_dir)
        _write_index_html(report_dir, zip_bytes)
        shutil.copytree(_app_dir() / "traceViewer", report_dir / "trace", dirs_exist_ok=True)
    except Exception as exc:  # звіт не повинен ламати запуск тестів
        tr = config.pluginmanager.get_plugin("terminalreporter")
        if tr:
            tr.write_line(f"Не вдалося створити Playwright-звіт: {exc!r}", red=True)
        return
    tr = config.pluginmanager.get_plugin("terminalreporter")
    if tr:
        shown = report_dir
        try:
            shown = report_dir.relative_to(Path(config.invocation_params.dir))
        except ValueError:
            pass
        tr.write_line("")
        tr.write_line(f"Playwright-звіт: {shown}/index.html", green=True)
        tr.write_line(f"Відкрити: python3 -m http.server 9323 --directory {shown}"
                      "   і далі http://localhost:9323")

"""Step recording for the HTML report.

Wrap every logical step of a test in `with step(page, "description"):`.
For each step the helper records the name, result, duration and error, and
takes a screenshot of the page right after the step. pytest-html then shows
the steps and screenshots in the test's section of test_report.html.
"""

import base64
import html
import time
from contextlib import contextmanager

import pytest
from pytest_html import extras

STEPS_KEY = pytest.StashKey[list]()

# Steps of the test that is currently running (set by the autouse fixture).
_current = {"steps": None}


@pytest.fixture(autouse=True)
def _record_steps(request):
    steps = []
    request.node.stash[STEPS_KEY] = steps
    _current["steps"] = steps
    yield
    _current["steps"] = None


@contextmanager
def step(page, description):
    steps = _current["steps"]
    if steps is None:
        raise RuntimeError("step() can only be used inside a test")

    record = {"description": description, "passed": True, "error": "", "screenshot": None}
    start = time.perf_counter()
    try:
        yield
    except BaseException as exc:
        record["passed"] = False
        lines = str(exc).strip().splitlines()
        record["error"] = f"{type(exc).__name__}: {lines[0] if lines else ''}"
        raise
    finally:
        record["duration"] = time.perf_counter() - start
        try:
            record["screenshot"] = base64.b64encode(page.screenshot()).decode()
        except Exception as screenshot_error:  # the page may already be closed
            record["error"] = record["error"] or f"Screenshot failed: {screenshot_error}"
        steps.append(record)


def _steps_table(steps):
    rows = []
    for number, item in enumerate(steps, start=1):
        status = "PASSED" if item["passed"] else "FAILED"
        color = "#1a7f37" if item["passed"] else "#cf222e"
        rows.append(
            "<tr>"
            f"<td>{number}</td>"
            f"<td>{html.escape(item['description'])}</td>"
            f"<td style='color:{color};font-weight:bold'>{status}</td>"
            f"<td>{item['duration']:.2f} s</td>"
            f"<td>{html.escape(item['error'])}</td>"
            "</tr>"
        )
    return (
        "<table border='1' cellpadding='4' style='border-collapse:collapse'>"
        "<tr><th>#</th><th>Step</th><th>Result</th><th>Duration</th><th>Error</th></tr>"
        + "".join(rows)
        + "</table>"
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return

    steps = item.stash.get(STEPS_KEY, [])
    if not steps:
        return

    new_extras = [extras.html(_steps_table(steps))]
    for number, item_step in enumerate(steps, start=1):
        if item_step["screenshot"]:
            new_extras.append(
                extras.png(
                    item_step["screenshot"],
                    name=f"Step {number}: {item_step['description']}",
                )
            )
    report.extras = getattr(report, "extras", []) + new_extras

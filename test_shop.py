import re

from playwright.sync_api import Page, expect

from step_report import step

BASE_URL = "https://www.saucedemo.com/"
USERNAME = "standard_user"
PASSWORD = "secret_sauce"


def login(page: Page) -> None:
    # Open the login page
    with step(page, "Open the login page"):
        page.goto(BASE_URL)
        expect(page.locator("[data-test='login-button']")).to_be_visible()

    # Enter the credentials
    with step(page, f"Enter username '{USERNAME}' and password"):
        page.locator("[data-test='username']").fill(USERNAME)
        expect(page.locator("[data-test='username']")).to_have_value(USERNAME)
        page.locator("[data-test='password']").fill(PASSWORD)
        expect(page.locator("[data-test='password']")).to_have_value(PASSWORD)

    # Submit the form
    with step(page, "Click Login and check the product list opens"):
        page.locator("[data-test='login-button']").click()
        expect(page.locator("[data-test='title']")).to_have_text("Products")


def test_login(page: Page) -> None:
    # Log in
    login(page)

    # Check thad

def test_purchase(page: Page) -> None:
    # Log in
    login(page)

    # Add the two products to the cart
    with step(page, "Add 'Sauce Labs Backpack' to the cart"):
        page.locator("[data-test='add-to-cart-sauce-labs-backpack']").click()
        expect(page.locator("[data-test='remove-sauce-labs-backpack']")).to_be_visible()
dacator("[data-test='add-to-cart-sauce-labs-bolt-t-shirt']").click()
        expect(page.locator("[data-test='remove-sauce-labs-bolt-t-shirt']")).to_be_visible()

    # Check the cart badge shows 2 items
    with step(page, "Check the cart badge shows 2 items"):
        expect(page.locator("[data-test='shopping-cart-badge']")).to_have_text("2")

    # Open the cart
    with step(page, "Open the cart"):
        page.locator("[data-test='shopping-cart-link']").click()
        expect(page).to_have_url(re.compile(r".*/cart\.html$"))
        expect(page.locator("[data-test='title']")).to_have_text("Your Cart")
adst='inventory-item-name']")
        expect(cart_items).to_have_count(2)
        expect(cart_items).to_have_text(["Sauce Labs Backpack", "Sauce Labs Bolt T-Shirt"])

    # Start checkout
    with step(page, "Click Checkout"):
        page.locator("[data-test='checkout']").click()
        expect(page).to_have_url(re.compile(r".*/checkout-step-one\.html$"))

    # Fill in the customer information (invented data)
    with step(page, "Fill in first name, last name and zip code (Ivan, Petrov, 12345)"):
        page.locator("[data-test='firstName']").fill("Ivan")
        expect(page.locator("[data-test='firstName']")).to_have_value("Ivan")
        page.locator("[data-test='lastName']").fill("Petrov")
        expect(page.locator("[data-test='lastName']")).to_have_value("Petrov")
        page.locator("[data-test='postalCode']").fill("12345")
        expect(page.locator("[data-test='postalCode']")).to_have_value("12345")

   ad"Click Continue and check the checkout overview opens"):
        page.locator("[data-test='continue']").click()
        expect(page).to_have_url(re.compile(r".*/checkout-step-two\.html$"))
        expect(page.locator("[data-test='title']")).to_have_text("Checkout: Overview")

    # Finish the order
    with step(page, "Click Finish"):
        page.locator("[data-test='finish']").click()
        expect(page).to_have_url(re.compile(r".*/checkout-complete\.html$"))

    # Check the success message
    with step(page, "Check the success message 'Thank you for your order!'"):
        expect(page.locator("[data-test='complete-header']")).to_have_text(
            "Thank you for your order!"
        )


def test_logout(page: Page) -> None:
    # Log in
    login(page)

    # Open the side menu
    with step(page, "Open the side menu"):
        page.locator("#react-burger-menu-btn").click()
        expect(page.locator("[data-test='logout-sidebar-link']")).to_be_visible()

    # Log out
    with step(page, "Click Logout"):
        page.locator("[data-test='logout-sidebar-link']").click()

    # Check that the login form is visible again
    with step(page, "Check the login form is visible again"):
        expect(page).to_have_url(BASE_URL)
        expect(page.locator("[data-test='login-button']")).to_be_visible()
        expect(page.locator("[data-test='username']")).to_be_visible()
        expect(page.locator("[data-test='password']")).to_be_visible()

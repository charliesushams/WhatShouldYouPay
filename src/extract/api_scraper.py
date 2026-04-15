from playwright.sync_api import sync_playwright, Playwright
import logging

"""
This script handles extracting json data from API calls 

"""
results = []

logger = logging.getLogger(__name__)


class ErrorAPIParser(Exception):
    """Raised when issues with Playwright retreiving data from API call"""

    pass


def handle_response(response):
    if "batch?" in response.url:  # matching specific endpoint
        try:
            logger.debug(
                "Response Status: %d from url: %s", response.status, response.url
            )
            data = response.json()
            results.append(data)
        except Exception as e:
            raise ErrorAPIParser("Error in handling json data from api call") from e


def run(playwright: Playwright, url: str):
    browser = playwright.chromium.launch()
    page = browser.new_page()
    page.on("response", handle_response)  # attach listener before navigation
    page.goto(url)
    page.wait_for_load_state("networkidle")
    browser.close()


def extracter(url: str) -> list:
    with sync_playwright() as playwright:
        run(playwright, url)
        return results


def main():
    pass


if __name__ == "main":
    main()

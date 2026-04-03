from playwright.sync_api import sync_playwright, Playwright

"""
This script handles extracting json data from api calls 

"""

def handle_response(response):
    results = []
    if "batch?" in response.url:  # matching specific endpoint
        try:
            print("<<", response.status, response.url)
            data = response.json()
            results.append(data)
        except Exception as e:
            print(f"Error in handling json data from craigslist: {e}")


def run(playwright: Playwright):
    browser = playwright.chromium.launch()
    page = browser.new_page()
    page.on("response", handle_response)  # attach listener before navigation
    page.goto("https://vancouver.craigslist.org/search/apa")
    page.wait_for_load_state("networkidle")
    browser.close()

def main():
    with sync_playwright() as playwright:
        run(playwright)

if __name__ == "main":
    main()
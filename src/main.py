import logging
import os
from extract import api_scraper
import pandas as pd
from transform import api_transformer, config

logger = logging.getLogger(__name__)


def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # Console: only show INFO and above
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)

    # File: capture everything including DEBUG
    file = logging.FileHandler("../logs/main.log")
    file.setLevel(logging.DEBUG)
    file.setFormatter(fmt)

    root.addHandler(console)
    root.addHandler(file)


def main():

    setup_logging()
    api_output = api_scraper.extracter(os.getenv("URL")) # type: ignore
    rows = []
    failed_count = 0

    for api_batch_data in api_output:
        listings = api_batch_data["data"]["batch"]
        
        for listing in listings:
            try:
                cleaned_listing = api_transformer.extract_row(listing)
                rows.append(cleaned_listing)
                logger.debug("Successfully extracted listing: %s", cleaned_listing["title"])
            except api_transformer.ListingDataError as e:
                logger.warning("Skipping malformed listing %s | %s", listing[config.IDX_TITLE], e)
                failed_count += 1

    listing_df = pd.DataFrame(rows).drop_duplicates()
    
    print(f"Successfully processed {len(listing_df)} listings with {failed_count} skipped listings")
    
if __name__ == "__main__":
    main()

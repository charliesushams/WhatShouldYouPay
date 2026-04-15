import logging
import os
from extract import api_scraper, html_scraper
from transform import api_transformer, config
from load import db
import pandas as pd


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
    file = logging.FileHandler("../logs/main.log", encoding="utf-8")
    file.setLevel(logging.DEBUG)
    file.setFormatter(fmt)

    root.addHandler(console)
    root.addHandler(file)


def main():

    setup_logging()
    logger.info("Connecting to API endpoint...")
    api_output = api_scraper.extracter(os.getenv("URL"))  # type: ignore
    rows = []
    json_cleaned_listings = []
    failed_count = 0

    logger.info("Starting listing extraction...")

    for api_batch_data in api_output:
        listings = api_batch_data["data"]["batch"]

        for listing in listings:
            try:
                cleaned_listing = api_transformer.extract_row(listing)
                rows.append(cleaned_listing)
                logger.debug(
                    "Successfully extracted listing: %s", cleaned_listing["title"]
                )
            except api_transformer.ListingDataError as e:
                logger.debug(
                    "Skipping malformed listing %s | %s", listing[config.IDX_TITLE], e
                )
                failed_count += 1

    listing_df = pd.DataFrame(rows)
    logger.info(
        "Successfully processed %d listings with %d skipped listings",
        len(listing_df),
        failed_count,
    )
    cleaned_listing_df = listing_df.drop_duplicates(
        subset=["title", "price", "sqft", "bedrooms"]
    )
    logger.info(
        "number of duplicate entries found: %d",
        len(listing_df) - len(cleaned_listing_df),
    )

    try:
        html_tree = html_scraper.get_html(os.getenv("URL"))  # type: ignore

        try:
            json_listings = html_scraper.json_listing_data(html_tree)

            for listing in json_listings:
                try:
                    formatted_listing = html_scraper.json_formatter(listing)
                    json_cleaned_listings.append(formatted_listing)
                except html_scraper.ListingDataError as e:
                    logger.debug("%s | skipping listing", e)

        except html_scraper.ListingsParseError as e:
            logger.warning("%s | No data to merge with api data", e)

    except RuntimeError as e:
        logger.warning(
            "%s | unable to retrieve html tree from requested URL: %s",
            e,
            os.getenv("URL"),
        )

    if json_cleaned_listings:
        json_listings_df = pd.DataFrame(json_cleaned_listings)
        cleaned_json_listings_df = json_listings_df.drop_duplicates()
        merged_df = pd.merge(
            cleaned_listing_df,
            cleaned_json_listings_df,
            on=["title", "bedrooms"],
            how="left",
        )
        merged_df.drop_duplicates(subset="id", inplace=True)
        # create new columns to support derived change in price column in database
        merged_df['original_price'] = merged_df['price']
        merged_df['current_price'] = merged_df['price']
        
        #convert to list of dicts to allow for custom SQLAlchemy Upsert Logic
        records = merged_df.to_dict(orient='records')
        
        db.save_listings_to_db(records)

    else:
        # upsert api data to db
        pass


if __name__ == "__main__":
    main()

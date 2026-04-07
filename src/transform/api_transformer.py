from transform import config
import logging

logger = logging.getLogger(__name__)

class ListingDataError(Exception):
    """Raised when a listing is missing required fields"""

    pass

def price_formatter(price: str) -> float:

    try:
        cleaned_price = price.lstrip("$").replace(",", "")
        return float(cleaned_price)

    except ValueError as e:
        raise ListingDataError('Issue formatting price from "$xxxx" -> float') from e


def extract_row(listing: list) -> dict:
    try:
        
        features = find_feat_index(listing, config.IDX_NESTED_STATS)
        price = find_feat_index(listing, config.IDX_NESTED_PRICE)

        return {
            "listing_id": listing[config.IDX_LISTING_ID],
            "title": listing[config.IDX_TITLE],
            "bedrooms": features[-2],
            "sqft": features[-1],
            "price": price_formatter(price[-1])

        }
    except (IndexError, TypeError, ListingDataError) as e:
        raise ListingDataError("Error when processing listing") from e

def find_feat_index(listing: list, feat_constant: int) -> list:
    
    if feat_constant == 5:
        feat = "bed/sqft"
    elif feat_constant == 10:
        feat = "price"
    else:
        feat = "unknown feature requested...double check constants"
        
    for element in listing:
        if isinstance(element, list) and element and element[0] == feat_constant:
            return element
    
    raise ListingDataError("Unable to locate feature: %s", feat)
    

def main():
    pass



if __name__ == "__main__":
    main()
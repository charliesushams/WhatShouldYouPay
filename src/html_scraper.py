"""
This script handles fetching and formatting html and json-ld listing data from Craigslist
"""

# To-do: wrap retry logic via tenacity
# Listing data class or validation with pydantic

import json
import httpx
from selectolax.lexbor import LexborHTMLParser, LexborNode


class ListingDataError(Exception):
    """Raised when a listing is missing required fields"""

    pass


class ListingsParseError(Exception):
    """Raised when no listings found within html tree"""

    pass


def get_html(url: str) -> LexborHTMLParser:

    try:
        r = httpx.get(url)
        r.raise_for_status()

    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
        )

    return LexborHTMLParser(r.text)


def get_listings(html_tree: LexborHTMLParser) -> list:

    listings = html_tree.css(".cl-static-search-result")

    if not listings:
        raise ListingsParseError("No listings could be located within html tree")

    else:
        return listings


def parse_listing(listing_node: LexborNode) -> dict:
    """Takes listing from html and extracts necessary fields. Raises user defined ListingDataError in response to ValueErrors"""

    try:
        price = listing_node.css_first(".price", strict=True).text()
        formatted_price = price_formatter(price)
        title = listing_node.css_first(".title", strict=True).text()

    except (ValueError, ListingDataError) as e:
        raise ListingDataError("Missing required listing fields") from e

    link_node = listing_node.css_first("a")
    url = link_node.attributes.get("href") if link_node else None

    return {"title": title, "price": formatted_price, "url": url}


def price_formatter(price: str) -> int:

    try:
        cleaned_price = price.lstrip("$").replace(",", "")
        return int(cleaned_price)

    except ValueError as e:
        raise ListingDataError('Issue formatting price from "$xxxx" -> int') from e


def json_listing_data(html_tree: LexborHTMLParser) -> list:
    """Takes html as input and returns list of listings contained within the json-ld tag"""

    # Check to see if JSON-LD data exists
    try:
        json_ld = html_tree.css_first(
            "script#ld_searchpage_results", default="not-found", strict=True
        )
        json_data = json.loads(json_ld.text())
        json_listings = json_data["itemListElement"]

    except ValueError as e:
        raise ListingsParseError("Unable to locate JSON_LD data") from e

    return json_listings


def json_formatter(json_listing: dict) -> dict:
    """Takes listing entry from JSON-LD and returns formatted listing entry"""

    required_listing_keys = (
        ("name", "name"),
        ("latitude", "latitude"),
        ("numberOfBathroomsTotal", "bathrooms"),
        ("longitude", "longitude"),
    )
    optional_listing_keys = (
        ("numberOfBedrooms", "bedrooms"),
        ("@type", "property_type"),
    )
    formatted_listing = {}

    for css_class, dict_key in required_listing_keys:
        try:
            formatted_listing[dict_key] = json_listing["item"][css_class]

        except KeyError as e:
            raise ListingDataError(
                "Missing required information from JSON-LD listing entry"
            ) from e

    for css_class, dict_key in optional_listing_keys:
        try:
            formatted_listing[dict_key] = json_listing["item"][css_class]
        except KeyError:
            formatted_listing[dict_key] = None

    return formatted_listing

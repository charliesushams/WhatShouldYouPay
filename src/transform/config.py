"""Index constants for each Craigslist ad (list) that contain wanted data"""

IDX_LISTING_ID = 0  # Database ID
IDX_TITLE = 1  # Listing Title
IDX_NESTED_STATS = 5  # [5, 1, 0] - want last two: 1, 0 (bedrooms, sqft)
IDX_NESTED_PRICE = 10  # [10, "$1,650"] - want last one: "$1,650" (price)

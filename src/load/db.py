from datetime import datetime
import logging
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Session, DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.sqlite import insert as upsert

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Double check table columns, etc. 
class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    original_price: Mapped[int]
    current_price: Mapped[int]
    sqft: Mapped[int]
    latitude: Mapped[float] = mapped_column(nullable=True)
    longitude: Mapped[float] = mapped_column(nullable=True)
    bedrooms: Mapped[int] = mapped_column(nullable=True)
    bathrooms: Mapped[int] = mapped_column(nullable=True)
    property_type: Mapped[str] = mapped_column(String(30), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime, server_default = func.CURRENT_TIMESTAMP())
    last_seen: Mapped[datetime] = mapped_column(DateTime, server_default = func.CURRENT_TIMESTAMP())


engine = create_engine("sqlite:///../data/listings.db")

Base.metadata.create_all(engine)

def save_listings_to_db(records: list[dict]):
    
    with Session(engine) as session:
        
        stmt = upsert(Listing)
        
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['id'],
            set_={
                'current_price': stmt.excluded.current_price, # in case of price changes
                'last_seen': func.CURRENT_TIMESTAMP() # update existing rows with batch timestamp
            }
        )
        
        session.execute(upsert_stmt, records)
        session.commit()

    logger.info("Successfully pushed %d records to listings database", len(records))
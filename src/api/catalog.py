from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()
        print(f"gold {first_row.gold}")
        print(f"red ml {first_row.red_ml}")

    # Can return a max of 20 items.

        return [
                {
                    "sku": "RED_POTION_0",
                    "name": "red potion",
                    "quantity": 1,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                }
            ]

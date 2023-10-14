from fastapi import APIRouter
import sqlalchemy
from src import database as db
from src.discord import log


router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog = []
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT sku, name, quantity, price, potion_type FROM catalog"))
    #Can return a max of 20 items.
        for sku, name, quantity, price, potion_type in result:
          if quantity > 0:
            catalog.append(
              {
                "sku": sku,
                "name": name,
                "quantity": quantity,
                "price": price,
                "potion_type":potion_type 
              }
            )
        log("Catalog Log:", catalog)
        return catalog

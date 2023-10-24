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
        result = connection.execute(sqlalchemy.text("""
        SELECT catalog.id, sku, name, price, potion_type, SUM(change) AS quantity
        FROM catalog
        JOIN potion_ledger ON catalog.id = catalog_id
        GROUP BY catalog.id
        """))

    #Can return a max of 20 items.
    for id, sku, name, price, potion_type, quantity in result:
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

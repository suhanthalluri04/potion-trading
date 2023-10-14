from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from src.discord import log


router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    log("Barrels Delivered Log:", barrels_delivered)
    with db.engine.begin() as connection:
      for barrel in barrels_delivered:
        result = connection.execute(sqlalchemy.text("SELECT gold, num_red_ml, num_blue_ml, num_green_ml FROM global_inventory"))
        first_row = result.first()
        goldNew = first_row.gold - (barrel.quantity * barrel.price)
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {goldNew} "))
        if barrel.sku == "SMALL_RED_BARREL":
          mLnew = first_row.num_red_ml + (barrel.quantity * barrel.ml_per_barrel)
          connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {mLnew} "))
        elif barrel.sku == "SMALL_BLUE_BARREL":
          mLnew = first_row.num_blue_ml + (barrel.quantity * barrel.ml_per_barrel)
          connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = {mLnew} "))
        elif barrel.sku == "SMALL_GREEN_BARREL":
          mLnew = first_row.num_green_ml + (barrel.quantity * barrel.ml_per_barrel)
          connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {mLnew} "))
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    log("Wholesale Catalog Log:", wholesale_catalog)
    with db.engine.begin() as connection:
      currgold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first().gold
      result = connection.execute(sqlalchemy.text("SELECT sku, quantity FROM catalog")).all()
      quantity = 0
      plan = []
      for barrel in wholesale_catalog:
         if barrel.sku == "SMALL_BLUE_BARREL":
            if result[1][1] < 10 and currgold >= barrel.price:
              currgold -= 120
              plan.append(
                {
                    "sku": "SMALL_BLUE_BARREL",
                    "quantity": 1,
                }
              )
         if barrel.sku == "SMALL_GREEN_BARREL":
            if result[2][1] < 10 and currgold >= barrel.price:
              currgold -= 100
              plan.append(
                {
                    "sku": "SMALL_GREEN_BARREL",
                    "quantity": 1,
                }
              )
         if barrel.sku == "SMALL_RED_BARREL":
            if result[0][1] < 10 and currgold >= barrel.price:
              currgold -= 100
              plan.append(
                {
                    "sku": "SMALL_RED_BARREL",
                    "quantity": 1,
                }
              )
      log("Planned Barrel Buy Log:", plan)
      return plan

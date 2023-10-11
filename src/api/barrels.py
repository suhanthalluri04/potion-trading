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
    print("Barrels Delivered Log:", barrels_delivered)
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
        #only one barrel purchased at a time as of now, will have to change this later
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("Wholesale Catalog Log:", wholesale_catalog)
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text("SELECT gold, num_red_potions, num_blue_potions, num_green_potions FROM global_inventory"))
      first_row = result.first()
      currgold = first_row.gold
      quantity = 0
      plan = []
      for barrel in wholesale_catalog:
         if barrel.sku == "SMALL_BLUE_BARREL":
            if first_row.num_blue_potions < 10 and currgold >= barrel.price:
              currgold -= 120
              plan.append(
                {
                    "sku": "SMALL_BLUE_BARREL",
                    "quantity": 1,
                }
              )
         if barrel.sku == "SMALL_RED_BARREL":
            if first_row.num_red_potions < 10 and currgold >= barrel.price:
              currgold -= 100
              plan.append(
                {
                    "sku": "SMALL_RED_BARREL",
                    "quantity": 1,
                }
              )
         if barrel.sku == "SMALL_GREEN_BARREL":
            if first_row.num_green_potions < 10 and currgold >= barrel.price:
              currgold -= 100
              plan.append(
                {
                    "sku": "SMALL_GREEN_BARREL",
                    "quantity": 1,
                }
              )
      print("Planned Barrel Buy Log:", plan)
      return plan

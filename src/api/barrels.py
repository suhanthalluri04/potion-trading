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
    newRed = 0
    newGreen = 0
    newBlue = 0
    newDark = 0
    goldPaid = 0
    for barrel in barrels_delivered:
      goldPaid = (barrel.quantity * barrel.price)
      if barrel.sku == "SMALL_RED_BARREL":
        newRed += barrel.quantity * barrel.ml_per_barrel
      elif barrel.sku == "SMALL_GREEN_BARREL":
        newGreen += barrel.quantity * barrel.ml_per_barrel
      elif barrel.sku == "SMALL_BLUE_BARREL":
        newBlue += barrel.quantity * barrel.ml_per_barrel
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text(
         """
        UPDATE global_inventory SET
        gold = gold - :goldPaid,
        num_red_ml = num_red_ml + :newRed,
        num_blue_ml = num_blue_ml + :newBlue,
        num_green_ml = num_green_ml + :newGreen
        """
      ),[{"newRed": newRed, "goldPaid": goldPaid, "newBlue": newBlue, "newGreen": newGreen,}])

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    log("Wholesale Catalog Log:", wholesale_catalog)
    with db.engine.begin() as connection:
      greenBought = False
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
            print(result[2][1],barrel.price, currgold)
            if result[2][1] < 10 and currgold >= barrel.price:
              greenBought = True
              currgold -= 100
              plan.append(
                {
                    "sku": "SMALL_GREEN_BARREL",
                    "quantity": 1,
                }
              )
         if barrel.sku == "SMALL_RED_BARREL" and greenBought:
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

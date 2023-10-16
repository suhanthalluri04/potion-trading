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
    for barrel in barrels_delivered:
      newGreen = barrel.potion_type[1] * barrel.ml_per_barrel
      newBlue = barrel.potion_type[2] * barrel.ml_per_barrel
      newRed = barrel.potion_type[0] * barrel.ml_per_barrel
      newDark = barrel.potion_type[3] * barrel.ml_per_barrel
      goldPaid = (barrel.quantity * barrel.price)
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
      plan = []
      for barrel in wholesale_catalog:
         if barrel.sku == "MINI_BLUE_BARREL":
            if currgold >= barrel.price:
              currgold -= barrel.price
              plan.append(
                {
                    "sku": barrel.sku,
                    "quantity": 1,
                }
              )
        #  if barrel.sku == "SMALL_GREEN_BARREL":
        #     if currgold >= barrel.price:
        #       greenBought = True
        #       currgold -= 100
        #       plan.append(
        #         {
        #             "sku": "SMALL_GREEN_BARREL",
        #             "quantity": 1,
        #         }
        #       )
         if barrel.sku == "MINI_RED_BARREL":
            if currgold >= barrel.price:
              currgold -= barrel.price
              plan.append(
                {
                    "sku": barrel.sku,
                    "quantity": 1,
                }
              )
      log("Planned Barrel Buy Log:", plan)
      return plan

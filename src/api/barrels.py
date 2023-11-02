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
    newGreen = 0
    newBlue = 0
    newRed = 0
    newDark = 0
    goldPaid = 0
    for barrel in barrels_delivered:
      newGreen += (barrel.potion_type[1] * barrel.ml_per_barrel) * barrel.quantity
      newBlue += (barrel.potion_type[2] * barrel.ml_per_barrel) * barrel.quantity
      newRed += (barrel.potion_type[0] * barrel.ml_per_barrel) * barrel.quantity
      newDark += (barrel.potion_type[3] * barrel.ml_per_barrel) * barrel.quantity
      goldPaid -= (barrel.quantity * barrel.price)
    with db.engine.begin() as connection:
      t_id = connection.execute(sqlalchemy.text(
        """
        INSERT INTO transactions (description)
        VALUES(:desc)
        RETURNING id
        """
      ),[{"desc": ("Purchased" + str(barrels_delivered))}]).scalar_one()
      connection.execute(sqlalchemy.text(
        """
        INSERT INTO ml_ledger (transaction_id, red_change, green_change, blue_change, dark_change)
        VALUES(:t_id, :newRed, :newGreen, :newBlue, :newDark)
        """
      ),[{"t_id":t_id, "newRed": newRed, "newBlue": newBlue, "newGreen": newGreen, "newDark": newDark}])
    with db.engine.begin() as connection:
      connection.execute(sqlalchemy.text(
        """
        INSERT INTO gold_ledger (transaction_id, change)
        VALUES(:t_id, :goldPaid)
        """
      ),[{"goldPaid": goldPaid, "t_id": t_id}])
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    log("Wholesale Catalog Log:", wholesale_catalog)
    with db.engine.begin() as connection:
      greenBought = False
      currgold = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM gold_ledger")).scalar_one()
      plan = []
      #buy mini barrels
      # while currgold >= 60:
      for barrel in wholesale_catalog:
        print(barrel.price, currgold)
        
        if barrel.price <= currgold:
            currgold -= barrel.price
            plan.append(
              {
                  "sku": barrel.sku,
                  "quantity": 1
              }
            )
      log("Planned Barrel Buy Log:", plan)
      return plan

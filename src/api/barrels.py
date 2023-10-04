from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

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
    print(barrels_delivered)
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text("SELECT gold, num_red_ml FROM global_inventory"))
      first_row = result.first()
      goldNew = first_row.gold - (barrels_delivered[0].quantity * barrels_delivered[0].price)
      mLnew = first_row.num_red_ml + (barrels_delivered[0].quantity * barrels_delivered[0].ml_per_barrel)
      #only one barrel purchased at a time as of now, will have to change this later

      connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {goldNew} "))
      connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {mLnew} "))
      


    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text("SELECT gold, num_red_potions FROM global_inventory"))
      first_row = result.first()
      quantity = 0
      for barrel in wholesale_catalog:
         if barrel.potion_type == [1, 0, 0, 0]:
            #As a very basic initial logic, purchase a new small red potion barrel 
            #only if the number of potions in inventory is less than 10. 
            if first_row.num_red_potions < 10 and first_row.gold >= barrel.price:
              quantity = 1
      if quantity < 1:
         return []
      else:
        return [
            {
                "sku": "SMALL_RED_BARREL",
                "quantity": quantity,
            }
        ]

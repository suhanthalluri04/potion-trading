from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print("Potions Delivered Log:", potions_delivered)
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_blue_potions, num_green_potions,\
                                                   num_red_ml, num_green_ml, num_blue_ml FROM global_inventory"))
      first_row = result.first()
      for potion in potions_delivered:
        if potion.potion_type == [100, 0, 0, 0]:
          potNew = first_row.num_red_potions + (potion.quantity)
          mLnew = first_row.num_red_ml - (potion.quantity * 100)
          connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {potNew} "))
          connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {mLnew} "))
        elif potion.potion_type == [0, 100, 0, 0]:
          potNew = first_row.num_green_potions + (potion.quantity)
          mLnew = first_row.num_green_ml - (potion.quantity * 100)
          connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {potNew} "))
          connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {mLnew} "))
        elif potion.potion_type == [0, 0, 100, 0]:
          potNew = first_row.num_blue_potions + (potion.quantity)
          mLnew = first_row.num_blue_ml - (potion.quantity * 100)
          connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = {potNew} "))
          connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = {mLnew} "))
    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    plan = []
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_blue_ml, num_green_ml FROM global_inventory"))
      first_row = result.first()
      qtyRed = first_row.num_red_ml // 100
      qtyBlue = first_row.num_blue_ml // 100
      qtyGreen = first_row.num_green_ml // 100
      if qtyRed > 0:
        plan.append(
                {
                    "potion_type": [100, 0, 0, 0],
                    "quantity": qtyRed,
                }
        )
      if qtyBlue > 0:
        plan.append(
                {
                    "potion_type": [0, 0, 100, 0],
                    "quantity": qtyBlue,
                }
        )
      if qtyGreen > 0:
        plan.append(
                {
                    "potion_type": [0, 100, 0, 0],
                    "quantity": qtyGreen,
                }
        )

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    print("Bottling Plan Log:", plan)
    return plan
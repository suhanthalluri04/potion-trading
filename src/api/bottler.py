from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from src.discord import log


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
    log("Potions Delivered Log:", potions_delivered)
    with db.engine.begin() as connection:
      for potion in potions_delivered:
        lostGreen = potion.potion_type[1] * potion.quantity
        lostBlue = potion.potion_type[2] * potion.quantity
        lostRed = potion.potion_type[0] * potion.quantity
        lostDark = potion.potion_type[3] * potion.quantity
        connection.execute(sqlalchemy.text(
          """
          UPDATE global_inventory SET
          num_red_ml = num_red_ml - :lostRed,
          num_blue_ml = num_blue_ml - :lostBlue,
          num_green_ml = num_green_ml - :lostGreen
          """
        ),[{"lostRed": lostRed, "lostBlue": lostBlue, "lostGreen": lostGreen,}])
        connection.execute(sqlalchemy.text(
          """
          UPDATE catalog SET
          quantity = quantity + :newQuantity
          WHERE potion_type = :givenPotion_type
          """
        ),[{"newQuantity": potion.quantity, "givenPotion_type": potion.potion_type}])
    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    plan = []
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text("SELECT gold, num_red_ml, num_blue_ml, num_green_ml FROM global_inventory"))
      catalog = connection.execute(sqlalchemy.text("SELECT potion_type FROM catalog")).all()
      first_row = result.first()
      mlList = [first_row.num_red_ml, first_row.num_green_ml, first_row.num_blue_ml]
      # if qtyRed >= 1 and qtyBlue >= 1:
      #   quantity = min(qtyRed, qtyBlue)
      #   plan.append(
      #           {
      #               "potion_type": [50, 0, 50, 0],
      #               "quantity": quantity
      #           }
      #   )
      #ONLY BOTTLE NON full rbg
      for potion_type in catalog:
         potion_type = potion_type[0]
         if potion_type[0] != 100 and \
         potion_type[1] != 100 and \
         potion_type[2] != 100:
          if mlList[0] >= potion_type[0] and \
          mlList[1] >= potion_type[1] and \
          mlList[2] >= potion_type[2]:
            qtyBasedonML = []
            for i in range(len(potion_type)): 
              if potion_type[i] != 0:
                  qtyBasedonML.append(mlList[i] // potion_type[i])
            quantity = min(qtyBasedonML)   
            plan.append(
                    {
                        "potion_type": potion_type,
                        "quantity": quantity
                    }
            )
            for k in range(len(mlList)):
                mlList[k] -= potion_type[k] * quantity
      #only full RBG potions
      for potion_type in catalog:
         print(potion_type)
         potion_type = potion_type[0]
         if potion_type[0] == 100 or\
         potion_type[1] == 100 or \
         potion_type[2] == 100:
          if mlList[0] >= potion_type[0] and\
          mlList[1] >= potion_type[1] and \
          mlList[2] >= potion_type[2]:
            qtyBasedonML = []
            for i in range(len(potion_type)): 
              if potion_type[i] != 0:
                  print(i, potion_type[i], mlList[i])
                  qtyBasedonML.append(mlList[i] // potion_type[i])
            quantity = min(qtyBasedonML)   
            plan.append(
                    {
                        "potion_type": potion_type,
                        "quantity": quantity
                    }
            )
            for k in range(len(mlList)):
                mlList[k] -= potion_type[k] * quantity
      # if qtyRed > 0:
      #   plan.append(
      #           {
      #               "potion_type": [100, 0, 0, 0],
      #               "quantity": 1,
      #           }
      #   )
      # if qtyBlue > 0:
      #   plan.append(
      #           {
      #               "potion_type": [0, 0, 100, 0],
      #               "quantity": qtyBlue,
      #           }
      #   )
      # if qtyGreen > 0:
      #   plan.append(
      #           {
      #               "potion_type": [0, 100, 0, 0],
      #               "quantity": qtyGreen,
      #           }
      #   )
    log("Bottling Plan Log:", plan)
    return plan
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
    lostGreen = 0
    lostBlue = 0
    lostRed = 0
    lostDark = 0
    for potion in potions_delivered:
      lostGreen -= (potion.potion_type[1] * potion.quantity)
      lostBlue -= (potion.potion_type[2] * potion.quantity)
      lostRed -= (potion.potion_type[0] * potion.quantity)
      lostDark -= (potion.potion_type[3] * potion.quantity)
    with db.engine.begin() as connection:
      t_id = connection.execute(sqlalchemy.text(
        """
        INSERT INTO transactions (description)
        VALUES(:desc)
        RETURNING id
        """
      ),[{"desc": "Potions Bottled:" + str(potions_delivered)}]).scalar_one()
      connection.execute(sqlalchemy.text(
        """
        INSERT INTO ml_ledger (transaction_id, red_change, green_change, blue_change, dark_change)
        VALUES(:t_id, :lostRed, :lostGreen, :lostBlue, :lostDark)
        """
      ),[{"t_id": t_id, "lostRed": lostRed, "lostBlue": lostBlue, "lostGreen": lostGreen, "lostDark":lostDark}])
      for potion in potions_delivered:
        connection.execute(sqlalchemy.text(
          """
          INSERT INTO potion_ledger (transaction_id, catalog_id, change)
          SELECT :t_id, catalog.id, :change
          FROM catalog WHERE catalog.potion_type = :potion_type
          """
        ),[{"t_id" : t_id, "potion_type": potion.potion_type, "change": potion.quantity }])
    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    plan = []
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text(
         """SELECT SUM(red_change) num_red_ml, SUM(blue_change)num_blue_ml, SUM(green_change) num_green_ml, 
            SUM(dark_change) num_dark_ml FROM ml_ledger"""))
      catalog = connection.execute(sqlalchemy.text("SELECT potion_type FROM catalog")).all()
      numPots = connection.execute(sqlalchemy.text("SELECT SUM(change) as pots FROM potion_ledger")).scalar_one()
      SpaceLeft = 300 - numPots
      amntEach = SpaceLeft // 6
      log("NumPots, SpaceLeft, NumEach", (numPots, SpaceLeft, amntEach))
      log("Amnt After Bottle", numPots + amntEach*5)
      first_row = result.first()
      mlList = [first_row.num_red_ml, first_row.num_green_ml, first_row.num_blue_ml, first_row.num_dark_ml]
      #leave extra for multicolored potions
      for i in range(len(mlList)):
         if mlList[i] > 200:
            mlList[i] -= 100
      if SpaceLeft > 0:
        for potion_type in catalog:
          potion_type = potion_type[0]
          if potion_type[0] != 100 and \
          potion_type[1] != 100 and \
          potion_type[2] != 100 and \
          potion_type[3] != 100:
            if mlList[0] >= potion_type[0] and \
            mlList[1] >= potion_type[1] and \
            mlList[2] >= potion_type[2]:
              qtyBasedonML = []
              for i in range(len(potion_type)): 
                if potion_type[i] != 0:
                    qtyBasedonML.append(mlList[i] // potion_type[i])
              quantity = min(qtyBasedonML) if (min(qtyBasedonML) <= amntEach) else amntEach
              if quantity > 0: 
                print(potion_type[2])
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
          potion_type = potion_type[0]
          if potion_type[0] == 100 or\
          potion_type[1] == 100 or \
          potion_type[2] == 100 or \
            potion_type[3] == 100:
            if mlList[0] >= potion_type[0] and\
            mlList[1] >= potion_type[1] and \
            mlList[2] >= potion_type[2] and \
            mlList[3] >= potion_type[3]:
              qtyBasedonML = []
              for i in range(len(potion_type)): 
                if potion_type[i] != 0:
                    qtyBasedonML.append(mlList[i] // potion_type[i])
              quantity = min(qtyBasedonML) 
              quantity = min(qtyBasedonML) if (min(qtyBasedonML) <= amntEach) else amntEach
              if quantity > 0: 
                print(potion_type)
                plan.append(
                        {
                            "potion_type": potion_type,
                            "quantity": quantity
                        }
                )
              for k in range(len(mlList)):
                  mlList[k] -= potion_type[k] * quantity
    log("Bottling Plan Log:", plan)
    return plan
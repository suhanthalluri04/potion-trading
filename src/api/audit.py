from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db
from src.discord import log

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text("SELECT gold, num_blue_ml, num_green_ml, num_red_ml FROM global_inventory"))
      first_row = result.first()
      result2 = connection.execute(sqlalchemy.text("SELECT name, quantity FROM catalog"))
      potQuantities = {k:v for (k,v) in result2}
      totalml = first_row.num_red_ml + first_row.num_green_ml + first_row.num_blue_ml
      totalPot = sum(potQuantities.values())
      log("Audit: Current mL", f"Red: {first_row.num_red_ml}, Green: {first_row.num_green_ml}, Blue: {first_row.num_blue_ml}")
      log("Audit: Current Gold", f"Gold: {first_row.gold}")
      log("Audit: Current Potions", potQuantities)
    return {"number_of_potions": totalPot, "ml_in_barrels": totalml, "gold": first_row.gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"

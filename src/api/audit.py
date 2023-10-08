from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text("SELECT gold, num_red_potions, num_red_ml, num_blue_ml, num_blue_potions, num_green_ml, num_green_potions FROM global_inventory"))
      first_row = result.first()
      totalml = first_row.num_red_ml + first_row.num_green_ml + first_row.num_blue_ml #change this after other potions added
      totalPot = first_row.num_red_potions + first_row.num_green_potions + first_row.num_blue_potions
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

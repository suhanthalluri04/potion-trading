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
      totalGold = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM gold_ledger")).scalar_one()
      totalPot = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM potion_ledger")).scalar_one()
      totalml = connection.execute(sqlalchemy.text("SELECT SUM(red_change + blue_change + green_change + dark_change) FROM ml_ledger")).scalar_one()
      log("Audit: Current Gold", f"Gold: {totalGold}")
    return {"number_of_potions": totalPot, "ml_in_barrels": totalml, "gold": totalGold}

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

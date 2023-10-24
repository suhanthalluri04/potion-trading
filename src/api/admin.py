from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from src.discord import log

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
          """
          DELETE FROM potion_ledger
          """
        ))
        connection.execute(sqlalchemy.text(
          """
          DELETE FROM ml_ledger
          """
        ))
        connection.execute(sqlalchemy.text(
          """
          DELETE FROM gold_ledger
          """
        ))
        connection.execute(sqlalchemy.text(
          """
          DELETE FROM transactions
          """
        ))
        t_ids = connection.execute(sqlalchemy.text(
          """
          INSERT INTO transactions (description)
          VALUES
            ('gold init'),
            ('ml init'),
            ('potion init')
          RETURNING id
          """
        )).all()
        print(t_ids)
        connection.execute(sqlalchemy.text(
          """
          INSERT INTO gold_ledger (transaction_id, change)
          VALUES (:t_id, 100)
          """
        ), [{"t_id" : t_ids[0].id}])
        connection.execute(sqlalchemy.text(
          """
          INSERT INTO ml_ledger (transaction_id, red_change, green_change, blue_change, dark_change)
          VALUES (:t_id, 0, 0, 0, 0)
          """
        ), [{"t_id" : t_ids[1].id}])
        connection.execute(sqlalchemy.text(
          """
          INSERT INTO potion_ledger (transaction_id, catalog_id, change)
          VALUES 
            (:t_id, 1, 0),
            (:t_id, 2, 0),
            (:t_id, 3, 0),
            (:t_id, 4, 0),
            (:t_id, 5, 0),
            (:t_id, 6, 0)
          """
        ), [{"t_id" : t_ids[2].id}])
    log("Reset", "Burned to the Ground!")

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    # TODO: Change me!
    return {
        "shop_name": "Alluri Concoctions",
        "shop_owner": "Suhanth Alluri",
    }


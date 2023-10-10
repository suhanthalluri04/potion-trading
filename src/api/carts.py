from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str

carts = {}

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    #(id : name, qtyRed, qtyGreen, qtyBlue)
    id = hash(new_cart.customer)
    carts[id] = [new_cart.customer, 0, 0, 0]
    #new cart should be last cart in list

    return {"cart_id": id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    return {carts[cart_id]}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    if item_sku == "RED_POTION_0":
      carts[cart_id][1] = cart_item.quantity
    if item_sku == "GREEN_POTION_0":
      carts[cart_id][2] = cart_item.quantity
    if item_sku == "BLUE_POTION_0":
      carts[cart_id][3] = cart_item.quantity
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    print("payment:",cart_checkout.payment)
    print("Potions about to be Bought:", "Red:", carts[cart_id][1], "Green", carts[cart_id][2], "Blue", carts[cart_id][3])
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_blue_potions, num_green_potions, gold FROM global_inventory"))
      first_row = result.first()
      potionsBought = 0
      moneyPaid = 0
      if carts[cart_id][1] > first_row.num_red_potions\
          or carts[cart_id][2] > first_row.num_green_potions \
          or carts[cart_id][3] > first_row.num_blue_potions:
          print("Log: Not Enough Potions")
          raise HTTPException(status_code=400, detail="Not enough potions in stock.")
      else:
          result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_blue_potions, num_green_potions, gold FROM global_inventory"))
          first_row = result.first()
          potionsBought = carts[cart_id][1] + carts[cart_id][2] + carts[cart_id][3]
          moneyPaid = (50 * carts[cart_id][1]) + (1 * (carts[cart_id][2] + carts[cart_id][3]))
          newRedPot = first_row.num_red_potions - carts[cart_id][1]
          newGreenPot = first_row.num_green_potions - carts[cart_id][2]
          newBluePot = first_row.num_blue_potions - carts[cart_id][3]
          newGold = first_row.gold + moneyPaid
          connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {newRedPot}"))
          connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {newGreenPot}"))
          connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = {newBluePot}"))
          connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {newGold}"))

    return {"total_potions_bought": potionsBought, "total_gold_paid": moneyPaid}

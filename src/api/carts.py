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

carts = []

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    #(customer name, SKU, quantity)
    carts.append((new_cart.customer, 0, 0))

    return {"cart_id": len(carts) - 1}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    return {carts[cart_id]}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    carts[cart_id][1] = item_sku
    carts[cart_id][2] = cart_item.quantity


    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    print("payment:",cart_checkout.payment)
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text("SELECT num_red_potions, gold FROM global_inventory"))
      first_row = result.first()
      potionsBought = 0
      moneyPaid = 0
      if carts[cart_id][2] > first_row.num_red_potions:
          raise HTTPException(status_code=400, detail="Not enough potions in stock.")
      else:
          potionsBought = carts[cart_id][2]
          moneyPaid = (50 * carts[cart_id][2])
          newPot = first_row.num_red_potions - carts[cart_id][2]
          newGold = first_row.gold + moneyPaid
          connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {newPot}"))
          connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {newGold}"))

    return {"total_potions_bought": potionsBought, "total_gold_paid": moneyPaid}

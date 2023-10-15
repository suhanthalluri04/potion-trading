from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from src.discord import log


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
    with db.engine.begin() as connection:
      cart_id = connection.execute(sqlalchemy.text("INSERT INTO carts (customer_name) VALUES (:name) RETURNING cart_id"), [{"name": new_cart.customer}]).scalar()
    log("New Cart", cart_id)
    return cart_id

@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    return None


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
      connection.execute(sqlalchemy.text(
          """
          INSERT INTO cart_items (cart_id, catalog_id, quantity) 
          SELECT :cart_id, catalog_id, :quantity
          FROM catalog WHERE catalog.sku = :item_sku
          """), [{"cart_id": cart_id, "item_sku": item_sku, 'quantity': cart_item.quantity}])
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    potionsBought = 0
    with db.engine.begin() as connection:
      moneyPaid = 0
      potionsBought = connection.execute(sqlalchemy.text(
          """
          SELECT SUM(quantity)
          FROM cart_items
          WHERE cart_items.cart_id = :cart_id"""), [{"cart_id": cart_id }]).scalar()
      connection.execute(sqlalchemy.text(
          """
          UPDATE catalog
          SET quantity = catalog.quantity - cart_items.quantity
          FROM cart_items
          WHERE catalog.catalog_id = cart_items.catalog_id and cart_items.cart_id = :cart_id"""), [{"cart_id": cart_id }])
      cartItems = connection.execute(sqlalchemy.text(
          """
          SELECT catalog_id, quantity FROM cart_items
          WHERE cart_items.cart_id = :cart_id"""), [{"cart_id": cart_id }])
      for catalog_id, quantity in cartItems:
         moneyPaid += connection.execute(sqlalchemy.text(
          """
          UPDATE global_inventory
          SET gold = global_inventory.gold + (:quantity * catalog.price)
          FROM catalog
          WHERE catalog.catalog_id = :catalog_id
          RETURNING (:quantity * catalog.price)"""), [{"catalog_id": catalog_id, "quantity": quantity}]).scalar()
         
    log("Succesful Checkout", {"Potions Bought": potionsBought, "Money Paid" : moneyPaid})
    return {"total_potions_bought": potionsBought, "total_gold_paid": moneyPaid}

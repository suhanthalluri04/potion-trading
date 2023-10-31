from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from sqlalchemy import func
from src import database as db
from src.discord import log


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """
    log("Search page", search_page)
    log("sort col", sort_col)
    log("sort_order", sort_order)


    if search_page == "":
        sp = 1
    else:
        sp = int(search_page)
    metadata_obj = sqlalchemy.MetaData()
    carts = sqlalchemy.Table('carts', metadata_obj, autoload_with= db.engine)
    cart_items = sqlalchemy.Table('cart_items', metadata_obj, autoload_with= db.engine)
    catalog = sqlalchemy.Table('catalog', metadata_obj, autoload_with= db.engine)



    joined = sqlalchemy.select(
        carts.c.id,
        carts.c.customer_name,
        catalog.c.sku,
        cart_items.c.quantity,
        carts.c.created_at,
        carts.c.payment,
        (cart_items.c.quantity * catalog.c.price).label('total')
    ).select_from(
        carts
        .join(cart_items, carts.c.id == cart_items.c.cart_id)
        .join(catalog, cart_items.c.catalog_id == catalog.c.id)
    )


    if sort_col is search_sort_options.customer_name:
        order_by = joined.c.customer_name
    elif sort_col is search_sort_options.item_sku:
        order_by = joined.c.sku
    elif sort_col is search_sort_options.line_item_total:
        order_by = joined.c.total
    elif sort_col is search_sort_options.timestamp:
        order_by = joined.c.created_at

    stmt = (
        sqlalchemy.select(

            joined.c.id,
            joined.c.quantity,
            joined.c.sku,
            joined.c.total,
            joined.c.created_at,
            joined.c.customer_name
        )
        .select_from(joined)
        .limit(5)
    )

    if search_page != "":
        stmt = stmt.offset((int(search_page)-1)*5)

    
    if sort_order == search_sort_order.desc: 
        stmt = stmt.order_by(sqlalchemy.desc(order_by))
    elif sort_order == search_sort_order.asc:
        stmt = stmt.order_by(sqlalchemy.asc(order_by))
        

    # filter only if name parameter is passed
    if customer_name != "" and potion_sku != "":
        stmt = stmt.where((joined.c.customer_name.ilike(f"%{customer_name}%")) &
                          (joined.c.sku.ilike(f"%{potion_sku}%")) & (joined.c.payment == "gold card"))
    elif customer_name != "" and potion_sku == "":
        stmt = stmt.where(joined.c.customer_name.ilike(f"%{customer_name}%" & joined.c.payment == "gold card"))
    elif customer_name == "" and potion_sku != "":
        stmt = stmt.where(joined.c.sku.ilike(f"%{potion_sku}%" & joined.c.payment == "gold card"))
    

    with db.engine.connect() as conn:
        result = conn.execute(stmt)
        row_count = result.rowcount
        results = []
        for row in result:
            results.append(
                      {
                          "line_item_id": str(row.id),
                          "item_sku": str(row.quantity) + " " + row.sku + ("S" if row.quantity > 1 else ""),
                          "customer_name": row.customer_name,
                          "line_item_total": row.total,
                          "timestamp": row.created_at
                      }
                    )
        log("results", results)
        return(
              {
                  "previous": str(sp - 1) if sp > 1 else "",
                  "next": str(sp + 1) if (row_count - (sp * 5)) > 0  else "",
                  "results": results,
              }
        )


class NewCart(BaseModel):
    customer: str

carts = {}

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    with db.engine.begin() as connection:
      cart_id = connection.execute(sqlalchemy.text("INSERT INTO carts (customer_name) VALUES (:name) RETURNING id"), [{"name": new_cart.customer}]).scalar_one()
    log("New Cart", cart_id)
    return {"cart_id" : cart_id}

@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    return 


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
      connection.execute(sqlalchemy.text(
          """
          INSERT INTO cart_items (cart_id, catalog_id, quantity) 
          SELECT :cart_id, id, :quantity
          FROM catalog WHERE catalog.sku = :item_sku
          """), [{"cart_id": cart_id, "item_sku": item_sku, 'quantity': cart_item.quantity}])
    log("Cart Updated", {"Cart_id": cart_id, item_sku: cart_item.quantity})
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    potionsBought = 0
    with db.engine.begin() as connection:
      moneyPaid = 0
      isOrderPossible = connection.execute(sqlalchemy.text(
          """
          SELECT cart_items.catalog_id, cart_items.quantity 
          FROM cart_items
          JOIN catalog on catalog.id = cart_items.catalog_id
          JOIN (
            SELECT potion_ledger.catalog_id, SUM(change) as quantity
            FROM potion_ledger
            GROUP BY catalog_id 
          ) AS quantities on quantities.catalog_id = catalog.id
          WHERE cart_items.cart_id = :cart_id and quantities.quantity < cart_items.quantity
          """), [{"cart_id": cart_id }]).all()
      log("isOrderPossible", True if len(isOrderPossible) == 0 else False)  
      if len(isOrderPossible) == 0:
        potionsBought = connection.execute(sqlalchemy.text(
            """
            SELECT SUM(quantity)
            FROM cart_items
            WHERE cart_items.cart_id = :cart_id"""), [{"cart_id": cart_id }]).scalar()
        t_id = connection.execute(sqlalchemy.text(
            """
            INSERT INTO transactions (description)
            VALUES(:desc)
            RETURNING id
            """
          ),[{"desc": "Potions Bought:" + str(potionsBought)}]).scalar_one()
        connection.execute(sqlalchemy.text(
          """
          INSERT INTO potion_ledger (transaction_id, catalog_id, change)
          SELECT :t_id, catalog.id, SUM(cart_items.quantity)*(-1)
          FROM catalog
          JOIN cart_items on cart_items.catalog_id = catalog.id and cart_items.cart_id = :cart_id
          GROUP BY catalog.id
          """), [{"t_id": t_id, "cart_id": cart_id}])
        moneyPaid = connection.execute(sqlalchemy.text(
          """
          INSERT INTO gold_ledger (transaction_id, change)
          SELECT :t_id, SUM(cart_items.quantity * price)
          FROM catalog
          JOIN cart_items on cart_items.catalog_id = catalog.id and cart_items.cart_id = :cart_id
          RETURNING change
          """), [{"cart_id": cart_id, "t_id" : t_id}]).scalar_one()
        connection.execute(sqlalchemy.text(
            """
            UPDATE carts
            SET payment = :payment
            WHERE id = :cart_id"""), [{"payment": cart_checkout.payment, "cart_id": cart_id}])
        log("Succesful Checkout", {"Potions Bought": potionsBought, "Money Paid" : moneyPaid})
        return {"total_potions_bought": potionsBought, "total_gold_paid": moneyPaid}
      else:
         log("Order Cannot be Completed", isOrderPossible)
         raise HTTPException(status_code = 400, detail = "Not enough potions in stock. Order Cancelled")

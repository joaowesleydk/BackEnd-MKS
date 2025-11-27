from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.crud.crud import add_to_cart, get_cart_with_total, remove_from_cart, clear_cart
from app.schemas.schemas import CartItemCreate, User

router = APIRouter()

@router.get("/")
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_cart_with_total(db, current_user.id)

@router.post("/add")
def add_item_to_cart(
    item: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return add_to_cart(db, current_user.id, item)

@router.delete("/remove/{product_id}")
def remove_item_from_cart(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return remove_from_cart(db, current_user.id, product_id)

@router.delete("/clear")
def clear_user_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return clear_cart(db, current_user.id)
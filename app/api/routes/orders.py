from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.crud.crud import create_order, get_user_orders
from app.schemas.schemas import Order, OrderCreate, User

router = APIRouter()

@router.post("/", response_model=Order)
def create_new_order(
    order: OrderCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return create_order(db=db, order=order, user_id=current_user.id)

@router.get("/", response_model=List[Order])
def read_user_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_user_orders(db, user_id=current_user.id)
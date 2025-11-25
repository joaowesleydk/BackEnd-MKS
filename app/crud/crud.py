from sqlalchemy.orm import Session
from app.models.models import User, Product, Category, Order, OrderItem
from app.schemas.schemas import UserCreate, ProductCreate, CategoryCreate, OrderCreate
from app.core.security import get_password_hash

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, name=user.name, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Product).filter(Product.is_active == True).offset(skip).limit(limit).all()

def get_product(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()

def create_product(db: Session, product: ProductCreate):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_categories(db: Session):
    return db.query(Category).all()

def create_category(db: Session, category: CategoryCreate):
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def create_order(db: Session, order: OrderCreate, user_id: int):
    total = 0
    db_order = Order(user_id=user_id, total=0)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    for item in order.items:
        product = get_product(db, item.product_id)
        if product and product.stock >= item.quantity:
            item_total = product.price * item.quantity
            total += item_total
            
            db_item = OrderItem(
                order_id=db_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=product.price
            )
            db.add(db_item)
            
            product.stock -= item.quantity
    
    db_order.total = total
    db.commit()
    db.refresh(db_order)
    return db_order

def get_user_orders(db: Session, user_id: int):
    return db.query(Order).filter(Order.user_id == user_id).all()
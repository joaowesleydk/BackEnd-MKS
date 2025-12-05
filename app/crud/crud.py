from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.models import User, Product, Category, Order, OrderItem, Cart, CartItem
from app.schemas.schemas import UserCreate, ProductCreate, CategoryCreate, OrderCreate, CartItemCreate
from app.core.security import get_password_hash

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    try:
        # Tenta usar SQLAlchemy ORM primeiro
        return db.query(User).filter(User.email == email).first()
    except Exception:
        # Se falhar (coluna role não existe), usa SQL direto
        try:
            result = db.execute(text("""
                SELECT id, email, name, hashed_password, is_active, created_at
                FROM users WHERE email = :email
            """), {"email": email})
            row = result.fetchone()
            if row:
                user = User()
                user.id = row[0]
                user.email = row[1] 
                user.name = row[2]
                user.hashed_password = row[3]
                user.is_active = row[4] if row[4] is not None else True
                user.created_at = row[5]
                user.role = "user"  # Define role padrão
                return user
            return None
        except Exception:
            return None

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email, 
        name=user.name, 
        hashed_password=hashed_password,
        role="user"  # Define role padrão
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_products(db: Session, skip: int = 0, limit: int = 100, category_id: int = None, min_price: float = None, max_price: float = None, search: str = None):
    query = db.query(Product).filter(Product.is_active == True)
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    if search:
        query = query.filter(
            Product.name.ilike(f"%{search}%") | 
            Product.description.ilike(f"%{search}%")
        )
    
    return query.offset(skip).limit(limit).all()

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

def get_or_create_cart(db: Session, user_id: int):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

def add_to_cart(db: Session, user_id: int, item: CartItemCreate):
    cart = get_or_create_cart(db, user_id)
    
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == item.product_id
    ).first()
    
    if existing_item:
        existing_item.quantity += item.quantity
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(cart_item)
    
    db.commit()
    return get_cart_with_total(db, user_id)

def get_cart_with_total(db: Session, user_id: int):
    cart = get_or_create_cart(db, user_id)
    cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
    
    total = 0
    for item in cart_items:
        product = get_product(db, item.product_id)
        if product:
            total += product.price * item.quantity
    
    return {"cart": cart, "items": cart_items, "total": total}

def remove_from_cart(db: Session, user_id: int, product_id: int):
    cart = get_or_create_cart(db, user_id)
    item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == product_id
    ).first()
    
    if item:
        db.delete(item)
        db.commit()
    
    return get_cart_with_total(db, user_id)

def clear_cart(db: Session, user_id: int):
    cart = get_or_create_cart(db, user_id)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    return cart
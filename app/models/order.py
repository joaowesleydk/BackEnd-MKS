from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total = Column(Float, nullable=False)
    frete = Column(Float, default=0.0)
    status = Column(String, default="pending")  # pending, paid, shipped, delivered, cancelled
    payment_id = Column(String, nullable=True)  # Mercado Pago payment ID
    payment_method = Column(String, nullable=True)
    endereco = Column(JSON, nullable=False)
    items = Column(JSON, nullable=False)  # Lista de produtos e quantidades
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")
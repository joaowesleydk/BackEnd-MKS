from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(Text, nullable=True)
    preco = Column(Float, nullable=False)
    imagens = Column(JSON, default=[])
    categoria = Column(String, nullable=False)  # Feminina, Masculina, Cosméticos, Bijuterias
    promocao = Column(Boolean, default=False)
    preco_promocional = Column(Float, nullable=True)
    estoque = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
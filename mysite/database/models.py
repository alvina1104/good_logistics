from datetime import datetime, date
from mysite.database.db import Base
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, Boolean, Date, DateTime, ForeignKey, Enum, Numeric, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from decimal import Decimal


class RoleChoices(str, PyEnum):
    buyer = "buyer"
    seller = "seller"
    manager = "manager"
    courier = "courier"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(30), unique=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    password: Mapped[str] = mapped_column(String(50))
    status: Mapped[RoleChoices] = mapped_column(Enum(RoleChoices), default=RoleChoices.buyer)
    created_date: Mapped[date] = mapped_column(Date, default=date.today)

    review: Mapped[List["Review"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    order: Mapped[List["Order"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(String(500), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column(String(100), unique=True)

    store: Mapped[List["Store"]] = relationship(back_populates="category", cascade="all, delete-orphan")
    products: Mapped[List["Product"]] = relationship(back_populates="category", cascade="all, delete-orphan")


class Store(Base):
    __tablename__ = "store"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_name: Mapped[str] = mapped_column(String(50))
    store_image: Mapped[str] = mapped_column(String)

    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))
    category: Mapped["Category"] = relationship(back_populates="store")

    products: Mapped[List["Product"]] = relationship(back_populates="store")


class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    description: Mapped[str] = mapped_column(Text)
    is_original: Mapped[bool] = mapped_column(Boolean, default=False)
    create_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    store_id: Mapped[int] = mapped_column(ForeignKey("store.id"))
    store: Mapped["Store"] = relationship(back_populates="products")

    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))
    category: Mapped["Category"] = relationship(back_populates="products")

    review: Mapped[List["Review"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    order: Mapped[List["Order"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "review"
    __table_args__ = (
        CheckConstraint("stars >= 1 AND stars <= 5", name="check_review_stars"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(String(2000))
    stars: Mapped[int] = mapped_column(Integer, nullable=False)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="review")

    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))
    product: Mapped["Product"] = relationship(back_populates="review")


class City(Base):
    __tablename__ = "city"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city_name: Mapped[str] = mapped_column(String(50))

    order: Mapped[List["Order"]] = relationship(back_populates="city", cascade="all, delete-orphan")
    warehouse: Mapped[List["WareHouse"]] = relationship(back_populates="city", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))
    product: Mapped["Product"] = relationship(back_populates="order")

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="order")

    city_id: Mapped[int] = mapped_column(ForeignKey("city.id"))
    city: Mapped["City"] = relationship(back_populates="order")


class WareHouse(Base):
    __tablename__ = "warehouse"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sklad_code: Mapped[str] = mapped_column(String(50), unique=True)
    street: Mapped[str] = mapped_column(String(255))

    city_id: Mapped[int] = mapped_column(ForeignKey("city.id"))
    city: Mapped["City"] = relationship(back_populates="warehouse")

    deliver: Mapped[List["Deliver"]] = relationship(back_populates="warehouse", cascade="all, delete-orphan")


class Deliver(Base):
    __tablename__ = "deliver"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouse.id"))

    user: Mapped["User"] = relationship()
    warehouse: Mapped["WareHouse"] = relationship(back_populates="deliver")
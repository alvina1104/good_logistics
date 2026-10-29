from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from mysite.database.models import RoleChoices
from decimal import Decimal
from typing import Literal

class UserCreateSchema(BaseModel):
    username: str = Field(min_length=2, max_length=30)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    status: RoleChoices = RoleChoices.buyer


class UserLoginSchema(BaseModel):
    username: str
    password: str


class UserOutSchema(BaseModel):
    id: int
    username: str
    email: EmailStr
    status: RoleChoices
    created_date: date

    model_config = ConfigDict(from_attributes=True)


class UserUpdateSchema(BaseModel):
    username: str | None = Field(default=None, min_length=2, max_length=30)
    email: EmailStr | None = None


class CategoryCreateSchema(BaseModel):
    category_name: str = Field(min_length=1, max_length=100)

class CategoryOutSchema(BaseModel):
    id: int
    category_name: str

    model_config = ConfigDict(from_attributes=True)


class StoreCreateSchema(BaseModel):
    store_name: str = Field(min_length=1, max_length=50)
    store_image: str = Field(min_length=1)
    category_id: int = Field(gt=0)


class StoreOutSchema(BaseModel):
    id: int
    store_name: str
    store_image: str
    category_id: int

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    description: str
    is_original: bool = False
    store_id: int = Field(gt=0)
    category_id: int = Field(gt=0)


class ProductUpdate(BaseModel):
    product_name: str | None = Field(default=None, min_length=1, max_length=100)
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    description: str | None = None
    is_original: bool | None = None
    store_id: int | None = Field(default=None, gt=0)
    category_id: int | None = Field(default=None, gt=0)


class ProductOut(BaseModel):
    id: int
    product_name: str
    price: Decimal
    description: str
    is_original: bool
    create_date: datetime
    store_id: int
    category_id: int

    model_config = ConfigDict(from_attributes=True)



class ReviewCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    stars: int = Field(ge=1, le=5)
    product_id: int = Field(gt=0)


class ReviewOut(BaseModel):
    id: int
    text: str
    stars: int
    created_date: datetime
    user_id: int
    product_id: int

    model_config = ConfigDict(from_attributes=True)


class CityCreate(BaseModel):
    city_name: str = Field(min_length=1, max_length=50)


class CityOut(BaseModel):
    id: int
    city_name: str

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    product_id: int = Field(gt=0)
    city_id: int = Field(gt=0)
    quantity: int = Field(default=1, gt=0)


class OrderOut(BaseModel):
    id: int
    quantity: int
    total_price: Decimal
    created_date: datetime
    product_id: int
    user_id: int
    city_id: int

    model_config = ConfigDict(from_attributes=True)




class WareHouseCreate(BaseModel):
    sklad_code: str = Field(min_length=1, max_length=50)
    street: str = Field(min_length=1, max_length=255)
    city_id: int = Field(gt=0)


class WareHouseOut(BaseModel):
    id: int
    sklad_code: str
    street: str
    city_id: int

    model_config = ConfigDict(from_attributes=True)


class DeliverCreate(BaseModel):
    user_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)


class DeliverOut(BaseModel):
    id: int
    user_id: int
    warehouse_id: int

    model_config = ConfigDict(from_attributes=True)



class Action(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: Literal["create_product", "update_product", "delete_product"]
    data: dict


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=3000)
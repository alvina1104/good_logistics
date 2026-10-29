from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from mysite.api.auth import get_current_user
from mysite.database.db import get_db
from mysite.database.models import Product, User
from mysite.database.schema import ProductCreate, ProductUpdate, ProductOut, Action
from mysite.chains.tools import execute_action, get_product_or_404

product_router = APIRouter(prefix="/products", tags=["Products"])


def save_product_action(db: Session, user: User, action: Action):
    try:
        result = execute_action(db, user, action)
        db.commit()
        return result

    except ValidationError:
        db.rollback()
        raise HTTPException(422, "Некорректные данные товара")

    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Операция нарушает связи данных")

    except Exception:
        db.rollback()
        raise


@product_router.post("/", response_model=ProductOut, status_code=201)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    action = Action(operation="create_product",data=data.model_dump(mode="json"))

    result = save_product_action(db, current_user, action)
    return result["item"]


@product_router.get("/", response_model=list[ProductOut])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@product_router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return get_product_or_404(db, product_id)


@product_router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    action = Action(
        operation="update_product",
        data={
            "product_id": product_id,
            "changes": data.model_dump(mode="json", exclude_unset=True),
        },
    )

    result = save_product_action(db, current_user, action)
    return result["item"]


@product_router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    action = Action(operation="delete_product",data={"product_id": product_id})

    return save_product_action(db, current_user, action)
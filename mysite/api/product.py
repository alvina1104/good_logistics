from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.api.auth import get_current_user
from mysite.database.db import get_db
from mysite.database.models import Product, Store, Category, User, RoleChoices
from mysite.database.schema import ProductCreate, ProductUpdate, ProductOut

product_router = APIRouter(prefix="/products", tags=["Products"])


@product_router.post("/", response_model=ProductOut)
async def create_product(data: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status not in [RoleChoices.seller, RoleChoices.manager]:
        raise HTTPException(status_code=403, detail="Только seller или manager может добавить товар")
    if not db.query(Store).filter(Store.id == data.store_id).first():
        raise HTTPException(status_code=404, detail="Магазин не найден")
    if not db.query(Category).filter(Category.id == data.category_id).first():
        raise HTTPException(status_code=404, detail="Категория не найдена")
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@product_router.get("/", response_model=list[ProductOut])
async def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@product_router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return product


@product_router.put("/{product_id}", response_model=ProductOut)
async def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Пока только manager может изменить товар")
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    values = data.model_dump(exclude_unset=True)
    if "store_id" in values and not db.query(Store).filter(Store.id == values["store_id"]).first():
        raise HTTPException(status_code=404, detail="Магазин не найден")
    if "category_id" in values and not db.query(Category).filter(Category.id == values["category_id"]).first():
        raise HTTPException(status_code=404, detail="Категория не найдена")
    for key, value in values.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@product_router.delete("/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может удалить товар")
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    db.delete(product)
    db.commit()
    return {"message": "Товар успешно удалён"}

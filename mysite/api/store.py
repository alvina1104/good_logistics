from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.api.auth import get_current_user
from mysite.database.db import get_db
from mysite.database.models import Store, Category, User, RoleChoices
from mysite.database.schema import StoreCreateSchema, StoreOutSchema

store_router = APIRouter(prefix="/stores", tags=["Stores"])


@store_router.post("/", response_model=StoreOutSchema)
async def create_store(data: StoreCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status not in [RoleChoices.seller, RoleChoices.manager]:
        raise HTTPException(status_code=403, detail="Только seller или manager может создать магазин")
    if not db.query(Category).filter(Category.id == data.category_id).first():
        raise HTTPException(status_code=404, detail="Категория не найдена")
    store = Store(**data.model_dump())
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


@store_router.get("/", response_model=list[StoreOutSchema])
async def get_stores(db: Session = Depends(get_db)):
    return db.query(Store).all()


@store_router.get("/{store_id}", response_model=StoreOutSchema)
async def get_store(store_id: int, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Магазин не найден")
    return store


@store_router.put("/{store_id}", response_model=StoreOutSchema)
async def update_store(store_id: int, data: StoreCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status not in [RoleChoices.manager, RoleChoices.seller]:
        raise HTTPException(status_code=403, detail="Только manager и seller может изменить магазин")
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Магазин не найден")
    if not db.query(Category).filter(Category.id == data.category_id).first():
        raise HTTPException(status_code=404, detail="Категория не найдена")
    for key, value in data.model_dump().items():
        setattr(store, key, value)
    db.commit()
    db.refresh(store)
    return store


@store_router.delete("/{store_id}")
async def delete_store(store_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может удалить магазин")
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Магазин не найден")
    db.delete(store)
    db.commit()
    return {"message": "Магазин успешно удалён"}

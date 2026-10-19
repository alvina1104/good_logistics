
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.api.auth import get_current_user
from mysite.database.db import get_db
from mysite.database.models import Category, User, RoleChoices
from mysite.database.schema import CategoryCreateSchema, CategoryOutSchema

category_router = APIRouter(prefix="/categories", tags=["Categories"])


@category_router.post("/", response_model=CategoryOutSchema)
async def create_category(category: CategoryCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может создать категорию")
    if db.query(Category).filter(Category.category_name == category.category_name).first():
        raise HTTPException(status_code=400, detail="Такая категория уже существует")
    category_data = Category(category_name=category.category_name)
    db.add(category_data)
    db.commit()
    db.refresh(category_data)
    return category_data


@category_router.get("/", response_model=list[CategoryOutSchema])
async def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


@category_router.get("/{category_id}", response_model=CategoryOutSchema)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    return category


@category_router.put("/{category_id}", response_model=CategoryOutSchema)
async def update_category(category_id: int, category: CategoryCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может изменить категорию")
    category_db = db.query(Category).filter(Category.id == category_id).first()
    if not category_db:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    if db.query(Category).filter(Category.category_name == category.category_name, Category.id != category_id).first():
        raise HTTPException(status_code=400, detail="Такая категория уже существует")
    category_db.category_name = category.category_name
    db.commit()
    db.refresh(category_db)
    return category_db


@category_router.delete("/{category_id}")
async def delete_category(category_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может удалить категорию")
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    db.delete(category)
    db.commit()
    return {"message": "Категория успешно удалена"}

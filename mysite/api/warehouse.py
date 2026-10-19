from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.api.auth import get_current_user
from mysite.database.db import get_db
from mysite.database.models import WareHouse, City, User, RoleChoices
from mysite.database.schema import WareHouseCreate, WareHouseOut

warehouse_router = APIRouter(prefix="/warehouse", tags=["Warehouses"])


@warehouse_router.post("/", response_model=WareHouseOut)
async def create_warehouse(data: WareHouseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может создать склад")
    if not db.query(City).filter(City.id == data.city_id).first():
        raise HTTPException(status_code=404, detail="Город не найден")
    if db.query(WareHouse).filter(WareHouse.sklad_code == data.sklad_code).first():
        raise HTTPException(status_code=400, detail="Код склада уже существует")
    warehouse = WareHouse(**data.model_dump())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


@warehouse_router.get("/", response_model=list[WareHouseOut])
async def get_warehouses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status not in [RoleChoices.manager, RoleChoices.courier]:
        raise HTTPException(status_code=403, detail="Нет доступа к складам")
    return db.query(WareHouse).all()


@warehouse_router.get("/{warehouse_id}", response_model=WareHouseOut)
async def get_warehouse(warehouse_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status not in [RoleChoices.manager, RoleChoices.courier]:
        raise HTTPException(status_code=403, detail="Нет доступа к складам")
    warehouse = db.query(WareHouse).filter(WareHouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Склад не найден")
    return warehouse


@warehouse_router.put("/{warehouse_id}", response_model=WareHouseOut)
async def update_warehouse(warehouse_id: int, data: WareHouseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может изменить склад")
    warehouse = db.query(WareHouse).filter(WareHouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Склад не найден")
    if not db.query(City).filter(City.id == data.city_id).first():
        raise HTTPException(status_code=404, detail="Город не найден")
    for key, value in data.model_dump().items():
        setattr(warehouse, key, value)
    db.commit()
    db.refresh(warehouse)
    return warehouse


@warehouse_router.delete("/{warehouse_id}")
async def delete_warehouse(warehouse_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может удалить склад")
    warehouse = db.query(WareHouse).filter(WareHouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Склад не найден")
    db.delete(warehouse)
    db.commit()
    return {"message": "Склад успешно удалён"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.api.auth import get_current_user
from mysite.database.db import get_db
from mysite.database.models import Deliver, WareHouse, User, RoleChoices
from mysite.database.schema import DeliverCreate, DeliverOut

deliver_router = APIRouter(prefix="/deliver", tags=["Delivers"])


@deliver_router.post("/", response_model=DeliverOut)
async def create_deliver(data: DeliverCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может назначить доставку")
    courier = db.query(User).filter(User.id == data.user_id, User.status == RoleChoices.courier).first()
    if not courier:
        raise HTTPException(status_code=404, detail="Курьер не найден")
    if not db.query(WareHouse).filter(WareHouse.id == data.warehouse_id).first():
        raise HTTPException(status_code=404, detail="Склад не найден")
    deliver = Deliver(user_id=data.user_id, warehouse_id=data.warehouse_id)
    db.add(deliver)
    db.commit()
    db.refresh(deliver)
    return deliver


@deliver_router.get("/", response_model=list[DeliverOut])
async def get_delivers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status == RoleChoices.manager:
        return db.query(Deliver).all()
    if current_user.status == RoleChoices.courier:
        return db.query(Deliver).filter(Deliver.user_id == current_user.id).all()
    raise HTTPException(status_code=403, detail="Нет доступа к доставкам")


@deliver_router.get("/{deliver_id}", response_model=DeliverOut)
async def get_deliver(deliver_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    deliver = db.query(Deliver).filter(Deliver.id == deliver_id).first()
    if not deliver:
        raise HTTPException(status_code=404, detail="Доставка не найдена")
    if current_user.status != RoleChoices.manager and deliver.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой доставке")
    return deliver


@deliver_router.put("/{deliver_id}", response_model=DeliverOut)
async def update_deliver(deliver_id: int, data: DeliverCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может изменить назначение доставки")
    deliver = db.query(Deliver).filter(Deliver.id == deliver_id).first()
    if not deliver:
        raise HTTPException(status_code=404, detail="Доставка не найдена")
    courier = db.query(User).filter(User.id == data.user_id, User.status == RoleChoices.courier).first()
    if not courier:
        raise HTTPException(status_code=404, detail="Курьер не найден")
    if not db.query(WareHouse).filter(WareHouse.id == data.warehouse_id).first():
        raise HTTPException(status_code=404, detail="Склад не найден")
    deliver.user_id, deliver.warehouse_id = data.user_id, data.warehouse_id
    db.commit()
    db.refresh(deliver)
    return deliver


@deliver_router.delete("/{deliver_id}")
async def delete_deliver(deliver_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может удалить доставку")
    deliver = db.query(Deliver).filter(Deliver.id == deliver_id).first()
    if not deliver:
        raise HTTPException(status_code=404, detail="Доставка не найдена")
    db.delete(deliver)
    db.commit()
    return {"message": "Назначение доставки удалено"}

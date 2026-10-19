from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.api.auth import get_current_user
from mysite.database.db import get_db
from mysite.database.models import Order, Product, City, User, RoleChoices
from mysite.database.schema import OrderCreate, OrderOut

order_router = APIRouter(prefix="/orders", tags=["Orders"])


@order_router.post("/", response_model=OrderOut)
async def create_order(data: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.buyer:
        raise HTTPException(status_code=403, detail="Только buyer может создать заказ")
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    if not db.query(City).filter(City.id == data.city_id).first():
        raise HTTPException(status_code=404, detail="Город не найден")
    order = Order(product_id=product.id, city_id=data.city_id, quantity=data.quantity, total_price=product.price * data.quantity, user_id=current_user.id)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@order_router.get("/", response_model=list[OrderOut])
async def get_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status == RoleChoices.manager:
        return db.query(Order).all()
    if current_user.status == RoleChoices.buyer:
        return db.query(Order).filter(Order.user_id == current_user.id).all()
    raise HTTPException(status_code=403, detail="Нет доступа к заказам")


@order_router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    if current_user.status != RoleChoices.manager and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому заказу")
    return order



@order_router.delete("/{order_id}")
async def delete_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    if current_user.status != RoleChoices.manager and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому заказу")
    if current_user.status not in [RoleChoices.buyer, RoleChoices.manager]:
        raise HTTPException(status_code=403, detail="Нет доступа к удалению заказа")
    db.delete(order)
    db.commit()
    return {"message": "Заказ успешно удалён"}





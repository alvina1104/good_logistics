from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.api.auth import get_current_user
from mysite.database.db import get_db
from mysite.database.models import City, User, RoleChoices
from mysite.database.schema import CityCreate, CityOut

city_router = APIRouter(prefix="/city", tags=["Cities"])


@city_router.post("/", response_model=CityOut)
async def create_city(city: CityCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может создать город")
    if db.query(City).filter(City.city_name == city.city_name).first():
        raise HTTPException(status_code=400, detail="Такой город уже существует")
    city_data = City(city_name=city.city_name)
    db.add(city_data)
    db.commit()
    db.refresh(city_data)
    return city_data


@city_router.get("/", response_model=list[CityOut])
async def get_cities(db: Session = Depends(get_db)):
    return db.query(City).all()


@city_router.get("/{city_id}", response_model=CityOut)
async def get_city(city_id: int, db: Session = Depends(get_db)):
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="Город не найден")
    return city


@city_router.put("/{city_id}", response_model=CityOut)
async def update_city(city_id: int, data: CityCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может изменить город")
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="Город не найден")
    city.city_name = data.city_name
    db.commit()
    db.refresh(city)
    return city


@city_router.delete("/{city_id}")
async def delete_city(city_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может удалить город")
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="Город не найден")
    db.delete(city)
    db.commit()
    return {"message": "Город успешно удалён"}

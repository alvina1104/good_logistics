from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.api.auth import get_current_user
from mysite.database.db import get_db
from mysite.database.models import Review, Product, User, RoleChoices
from mysite.database.schema import ReviewCreate, ReviewOut

review_router = APIRouter(prefix="/reviews", tags=["Reviews"])


@review_router.post("/", response_model=ReviewOut)
async def create_review(data: ReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.buyer:
        raise HTTPException(status_code=403, detail="Только buyer может оставить отзыв")
    if not db.query(Product).filter(Product.id == data.product_id).first():
        raise HTTPException(status_code=404, detail="Товар не найден")
    review = Review(text=data.text, stars=data.stars, product_id=data.product_id, user_id=current_user.id)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@review_router.get("/", response_model=list[ReviewOut])
async def get_reviews(db: Session = Depends(get_db)):
    return db.query(Review).all()


@review_router.get("/{review_id}", response_model=ReviewOut)
async def get_review(review_id: int, db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    return review


@review_router.put("/{review_id}", response_model=ReviewOut)
async def update_review(review_id: int, data: ReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    if current_user.status != RoleChoices.manager and review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Можно изменить только свой отзыв")
    review.text, review.stars = data.text, data.stars
    db.commit()
    db.refresh(review)
    return review


@review_router.delete("/{review_id}")
async def delete_review(review_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    if current_user.status != RoleChoices.manager and review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Можно удалить только свой отзыв")
    db.delete(review)
    db.commit()
    return {"message": "Отзыв успешно удалён"}

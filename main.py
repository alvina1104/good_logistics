from fastapi import FastAPI
import uvicorn
from mysite.api import auth, user, category, city, deliver, order, product, review, store, warehouse, ai
from mysite.admin.setup import setup_admin


ware_app = FastAPI(title="Warehouse with AI")
ware_app.include_router(auth.auth_router)
ware_app.include_router(user.user_router)
ware_app.include_router(category.category_router)
ware_app.include_router(city.city_router)
ware_app.include_router(store.store_router)
ware_app.include_router(product.product_router)
ware_app.include_router(review.review_router)
ware_app.include_router(order.order_router)
ware_app.include_router(warehouse.warehouse_router)
ware_app.include_router(deliver.deliver_router)
ware_app.include_router(ai.ai_router)
setup_admin(ware_app)


if __name__ == "__main__":
    uvicorn.run(ware_app, host='127.0.0.1', port=8000)
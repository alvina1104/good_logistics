
from sqladmin import ModelView
from mysite.database.models import User, RefreshToken, Category, Store, Product, Review, City, Order, WareHouse, Deliver


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.email, User.status, User.created_date]
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.username, User.email]


class RefreshTokenAdmin(ModelView, model=RefreshToken):
    column_list = [RefreshToken.id, RefreshToken.user_id, RefreshToken.expires_at, RefreshToken.created_at]


class CategoryAdmin(ModelView, model=Category):
    column_list = [Category.id, Category.category_name]
    column_searchable_list = [Category.category_name]


class StoreAdmin(ModelView, model=Store):
    column_list = [Store.id, Store.store_name, Store.store_image, Store.category_id]
    column_searchable_list = [Store.store_name]


class ProductAdmin(ModelView, model=Product):
    column_list = [Product.id, Product.product_name, Product.price, Product.store_id, Product.category_id]
    column_searchable_list = [Product.product_name]


class ReviewAdmin(ModelView, model=Review):
    column_list = [Review.id, Review.user_id, Review.product_id, Review.stars, Review.created_date]


class CityAdmin(ModelView, model=City):
    column_list = [City.id, City.city_name]
    column_searchable_list = [City.city_name]


class OrderAdmin(ModelView, model=Order):
    column_list = [Order.id, Order.quantity, Order.total_price, Order.product_id, Order.user_id, Order.city_id, Order.created_date]


class WareHouseAdmin(ModelView, model=WareHouse):
    column_list = [WareHouse.id, WareHouse.sklad_code, WareHouse.street, WareHouse.city_id]


class DeliverAdmin(ModelView, model=Deliver):
    column_list = [Deliver.id, Deliver.user_id, Deliver.warehouse_id]

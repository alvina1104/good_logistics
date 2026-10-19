
from sqladmin import Admin
from mysite.database.db import engine
from mysite.admin.view import (
    UserAdmin, RefreshTokenAdmin, CategoryAdmin, StoreAdmin,
    ProductAdmin, ReviewAdmin, CityAdmin, OrderAdmin,
    WareHouseAdmin, DeliverAdmin
)


def setup_admin(app):
    admin = Admin(app, engine, title="MySite Admin")

    admin.add_view(UserAdmin)
    admin.add_view(RefreshTokenAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(StoreAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(ReviewAdmin)
    admin.add_view(CityAdmin)
    admin.add_view(OrderAdmin)
    admin.add_view(WareHouseAdmin)
    admin.add_view(DeliverAdmin)

    return admin

from decimal import Decimal
from fastapi import HTTPException
from langchain_core.tools import tool
from sqlalchemy import or_
from sqlalchemy.orm import Session
from mysite.database.models import Product, Store, Category, Order, User, RoleChoices
from mysite.database.schema import ProductCreate, ProductUpdate, ProductOut, Action


def product_to_dict(product: Product):
    return ProductOut.model_validate(product).model_dump(mode="json")


def get_product_or_404(db: Session, product_id: int):
    if product_id <= 0:
        raise HTTPException(422, "ID товара должен быть больше нуля")

    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Товар не найден")

    return product


def check_store_permission(db: Session, user: User, store_id: int):
    if user.status not in (RoleChoices.seller, RoleChoices.manager):
        raise HTTPException(403, "Только seller или manager может менять товары")

    store = db.get(Store, store_id)
    if not store:
        raise HTTPException(404, "Магазин не найден")

    if user.status == RoleChoices.seller:
        if store.owner_id != user.id:
            raise HTTPException(403, "Можно менять товары только своего магазина")

    return store


def search_products(
    db: Session,
    query: str = "",
    max_price: Decimal | None = None,
    store_id: int | None = None,
    category_id: int | None = None,
):
    products_query = db.query(Product)

    if query.strip():
        word = query.strip()
        products_query = products_query.filter(
            or_(
                Product.product_name.icontains(word, autoescape=True),
                Product.description.icontains(word, autoescape=True),
            )
        )

    if max_price is not None:
        if max_price <= 0:
            raise HTTPException(422, "Цена должна быть больше нуля")
        products_query = products_query.filter(Product.price <= max_price)

    if store_id is not None:
        if not db.get(Store, store_id):
            raise HTTPException(404, "Магазин не найден")
        products_query = products_query.filter(Product.store_id == store_id)

    if category_id is not None:
        if not db.get(Category, category_id):
            raise HTTPException(404, "Категория не найдена")
        products_query = products_query.filter(Product.category_id == category_id)

    total = products_query.count()
    products = products_query.order_by(Product.price, Product.id).limit(20).all()

    items = []
    for product in products:
        items.append(product_to_dict(product))

    return {
        "items": items,
        "total": total,
        "shown": len(items),
    }


def count_products(db: Session):
    return {
        "count": db.query(Product).count(),
        "unit": "товары в каталоге, не количество на складе",
    }


def get_product(db: Session, product_id: int):
    product = get_product_or_404(db, product_id)
    return {"items": [product_to_dict(product)]}


def compare_products(db: Session, product_ids: list[int]):
    if not 2 <= len(product_ids) <= 5:
        raise HTTPException(422, "Укажите от 2 до 5 товаров")

    if len(set(product_ids)) != len(product_ids):
        raise HTTPException(422, "ID товаров не должны повторяться")

    items = []
    for product_id in product_ids:
        product = get_product_or_404(db, product_id)
        items.append(product_to_dict(product))

    return {"items": items}


def list_stores(db: Session, user: User):
    stores = db.query(Store).order_by(Store.id).limit(100).all()
    result = []

    for store in stores:
        can_edit = False

        if user.status == RoleChoices.manager:
            can_edit = True
        elif user.status == RoleChoices.seller:
            can_edit = store.owner_id == user.id

        result.append({
            "id": store.id,
            "name": store.store_name,
            "category_id": store.category_id,
            "can_edit": can_edit,
        })

    return {"stores": result}


def list_categories(db: Session):
    categories = db.query(Category).order_by(Category.id).limit(100).all()
    result = []

    for category in categories:
        result.append({
            "id": category.id,
            "name": category.category_name,
        })

    return {"categories": result}


def validate_action(db: Session, user: User, action: Action):
    if user.status not in (RoleChoices.seller, RoleChoices.manager):
        raise HTTPException(403, "Нет прав на изменение товаров")

    if action.operation == "create_product":
        for field in action.data:
            if field not in ProductCreate.model_fields:
                raise HTTPException(422, f"Неизвестное поле: {field}")

        data = ProductCreate.model_validate(action.data)
        check_store_permission(db, user, data.store_id)

        if not db.get(Category, data.category_id):
            raise HTTPException(404, "Категория не найдена")

        return data.model_dump()

    if action.operation == "update_product":
        if set(action.data) != {"product_id", "changes"}:
            raise HTTPException(422, "Укажите product_id и changes")

    if action.operation == "delete_product":
        if user.status != RoleChoices.manager:
            raise HTTPException(403, "Только manager может удалить товар")

        if set(action.data) != {"product_id"}:
            raise HTTPException(422, "Укажите только product_id")

    product_id = action.data.get("product_id")
    if type(product_id) is not int:
        raise HTTPException(422, "product_id должен быть целым числом")

    product = get_product_or_404(db, product_id)
    check_store_permission(db, user, product.store_id)

    if action.operation == "update_product":
        changes = action.data["changes"]

        if not isinstance(changes, dict):
            raise HTTPException(422, "changes должен быть объектом")

        for field in changes:
            if field not in ProductUpdate.model_fields:
                raise HTTPException(422, f"Неизвестное поле: {field}")

        data = ProductUpdate.model_validate(changes)
        values = data.model_dump(exclude_unset=True)

        if not values:
            raise HTTPException(422, "Укажите поля для изменения")

        for value in values.values():
            if value is None:
                raise HTTPException(422, "Поля товара не могут быть null")

        if "store_id" in values:
            check_store_permission(db, user, values["store_id"])

        if "category_id" in values:
            if not db.get(Category, values["category_id"]):
                raise HTTPException(404, "Категория не найдена")

        return values

    order = db.query(Order).filter(Order.product_id == product.id).first()
    if order:
        raise HTTPException(409, "Нельзя удалить товар, связанный с заказами")

    return {}


def prepare_action(db: Session, user: User, action: Action):
    validate_action(db, user, action)

    result = {
        "requires_confirmation": True,
        "action": action.model_dump(mode="json"),
    }

    if action.operation != "create_product":
        product = get_product_or_404(db, action.data["product_id"])
        result["before"] = product_to_dict(product)

    return result


def execute_action(db: Session, user: User, action: Action):
    values = validate_action(db, user, action)

    if action.operation == "create_product":
        product = Product(**values)
        db.add(product)
        db.flush()
        db.refresh(product)

        return {
            "message": "Товар создан",
            "item": product_to_dict(product),
        }

    product = get_product_or_404(db, action.data["product_id"])

    if action.operation == "update_product":
        for key, value in values.items():
            setattr(product, key, value)

        db.flush()
        db.refresh(product)

        return {
            "message": "Товар изменён",
            "item": product_to_dict(product),
        }

    product_id = product.id
    db.delete(product)
    db.flush()

    return {
        "message": "Товар удалён",
        "product_id": product_id,
    }


def get_tools(db: Session, user: User):

    @tool
    def list_products_tool():
        """Показывает первые 20 товаров и общее количество товаров."""
        return search_products(db)

    @tool
    def search_products_tool(query: str):
        """Ищет товары по названию или описанию. Используй короткие слова."""
        return search_products(db, query=query)

    @tool
    def filter_products_tool(
        max_price: Decimal | None = None,
        store_id: int | None = None,
        category_id: int | None = None,
    ):
        """Фильтрует товары по цене, магазину и категории."""
        return search_products(
            db,
            max_price=max_price,
            store_id=store_id,
            category_id=category_id,
        )

    @tool
    def recommend_products_tool(query: str, max_price: Decimal | None = None):
        """Находит товары для рекомендации по запросу и бюджету."""
        return search_products(db, query=query, max_price=max_price)

    @tool
    def get_product_tool(product_id: int):
        """Показывает товар по его ID."""
        return get_product(db, product_id)

    @tool
    def count_products_tool():
        """Считает записи товаров в каталоге, не складские остатки."""
        return count_products(db)

    @tool
    def compare_products_tool(product_ids: list[int]):
        """Возвращает данные от 2 до 5 товаров для сравнения."""
        return compare_products(db, product_ids)

    @tool
    def list_stores_tool():
        """Показывает магазины и возможность менять их товары."""
        return list_stores(db, user)

    @tool
    def list_categories_tool():
        """Показывает категории товаров и их ID."""
        return list_categories(db)

    @tool
    def prepare_create_product_tool(data: ProductCreate):
        """Готовит создание товара для подтверждения. Не сохраняет товар."""
        action = Action(
            operation="create_product",
            data=data.model_dump(mode="json"),
        )
        return prepare_action(db, user, action)

    @tool
    def prepare_update_product_tool(product_id: int, changes: ProductUpdate):
        """Готовит изменение товара для подтверждения. Не меняет товар."""
        action = Action(
            operation="update_product",
            data={
                "product_id": product_id,
                "changes": changes.model_dump(mode="json", exclude_unset=True),
            },
        )
        return prepare_action(db, user, action)

    @tool
    def prepare_delete_product_tool(product_id: int):
        """Готовит удаление товара. Только manager. Не удаляет товар."""
        action = Action(
            operation="delete_product",
            data={"product_id": product_id},
        )
        return prepare_action(db, user, action)

    tools = [
        list_products_tool,
        search_products_tool,
        filter_products_tool,
        recommend_products_tool,
        get_product_tool,
        count_products_tool,
        compare_products_tool,
        list_stores_tool,
        list_categories_tool,
    ]

    if user.status in (RoleChoices.seller, RoleChoices.manager):
        tools.append(prepare_create_product_tool)
        tools.append(prepare_update_product_tool)

    if user.status == RoleChoices.manager:
        tools.append(prepare_delete_product_tool)

    return tools
import re
from decimal import Decimal

from fastapi import HTTPException
from langchain_core.tools import tool
from pydantic import ValidationError
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from mysite.database.models import Product, Store, Category, Order, User, RoleChoices
from mysite.database.schema import ProductCreate, ProductUpdate, ProductOut, Action


def product_to_dict(product: Product):
    """Товардын базадагы бардык ачык талааларын жана байланышкан аталыштарды кайтарат."""
    data = ProductOut.model_validate(product).model_dump(mode="json")
    data["store_name"] = product.store.store_name if product.store else None
    data["category_name"] = product.category.category_name if product.category else None
    return data


def get_product_or_404(db: Session, product_id: int):
    if type(product_id) is not int or product_id <= 0:
        raise HTTPException(422, "Неверный ID товара")
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(404, "Товар не найден")
    return product


def check_store_permission(db: Session, user: User, store_id: int):
    if user.status not in (RoleChoices.seller, RoleChoices.manager):
        raise HTTPException(403, "Недостаточно прав")
    store = db.get(Store, store_id)
    if store is None:
        raise HTTPException(404, "Магазин не найден")
    if user.status == RoleChoices.seller and store.owner_id != user.id:
        raise HTTPException(403, "Это не ваш магазин")
    return store


def has_ram(description: str, ram_gb: int) -> bool:
    """Ищет только RAM, а не SSD или другие значения GB."""
    ram = rf"{ram_gb}\s*(?:GB|ГБ)\b"
    patterns = [
        rf"\b(?:RAM|ОЗУ|оперативная память)\s*[:=\-]?\s*{ram}",
        rf"\b{ram}\s*(?:RAM|ОЗУ|оперативной памяти)\b",
    ]
    return any(re.search(p, description or "", re.IGNORECASE) for p in patterns)


def has_attribute(description: str, label: str, value: str) -> bool:
    """Проверяет явно записанные в описании атрибуты."""
    pattern = rf"\b(?:{label})\s*[:=\-]?\s*{re.escape(value)}\b"
    return bool(re.search(pattern, description or "", re.IGNORECASE))


def search_products(
    db: Session,
    query: str = "",
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    store_id: int | None = None,
    category_id: int | None = None,
    product_type: str | None = None,
    is_original: bool | None = None,
    ram_gb: int | None = None,
    color: str | None = None,
    size: str | None = None,
    strict_max: bool = False,
):
    if min_price is not None and min_price < 0:
        raise HTTPException(422, "Минимальная цена не может быть отрицательной")
    if max_price is not None and max_price < 0:
        raise HTTPException(422, "Максимальная цена не может быть отрицательной")
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(422, "Минимальная цена больше максимальной")
    if ram_gb is not None and ram_gb <= 0:
        raise HTTPException(422, "RAM должна быть больше нуля")

    products = db.query(Product).options(
        joinedload(Product.store), joinedload(Product.category)
    )

    # Универсальный поиск: никаких списков видов товаров в коде.
    if query.strip() or (product_type and product_type.strip()):
        products = products.join(Product.category)
        for word in [query.strip(), (product_type or "").strip()]:
            if not word:
                continue
            products = products.filter(or_(
                Product.product_name.icontains(word, autoescape=True),
                Product.description.icontains(word, autoescape=True),
                Category.category_name.icontains(word, autoescape=True),
            ))

    if min_price is not None:
        products = products.filter(Product.price >= min_price)
    if max_price is not None:
        products = products.filter(
            Product.price < max_price if strict_max else Product.price <= max_price
        )
    if store_id is not None:
        if db.get(Store, store_id) is None:
            raise HTTPException(404, "Магазин не найден")
        products = products.filter(Product.store_id == store_id)
    if category_id is not None:
        if db.get(Category, category_id) is None:
            raise HTTPException(404, "Категория не найдена")
        products = products.filter(Product.category_id == category_id)
    if is_original is not None:
        products = products.filter(Product.is_original == is_original)

    found = products.order_by(Product.price.asc(), Product.id.asc()).all()

    # Эти атрибуты пока есть только в description; неизвестное не считаем совпадением.
    if ram_gb is not None:
        found = [p for p in found if has_ram(p.description, ram_gb)]
    if color:
        found = [p for p in found if has_attribute(p.description, r"цвет|color", color)]
    if size:
        found = [p for p in found if has_attribute(p.description, r"размер|size", size)]

    items = [product_to_dict(p) for p in found]
    return {"items": items, "total": len(items), "shown": len(items)}


def count_products(db: Session):
    return {"count": db.query(Product).count(), "unit": "товары в каталоге"}


def get_product(db: Session, product_id: int):
    return {"items": [product_to_dict(get_product_or_404(db, product_id))]}


def compare_products(db: Session, product_ids: list[int]):
    if not 2 <= len(product_ids) <= 5 or len(set(product_ids)) != len(product_ids):
        raise HTTPException(422, "Укажите 2–5 разных ID товаров")
    return {"items": [product_to_dict(get_product_or_404(db, pid)) for pid in product_ids]}


def list_stores(db: Session, user: User):
    stores = db.query(Store).order_by(Store.id).all()
    return {"stores": [
        {
            "id": s.id, "name": s.store_name, "category_id": s.category_id,
            "can_edit": user.status == RoleChoices.manager or (
                user.status == RoleChoices.seller and s.owner_id == user.id
            ),
        }
        for s in stores
    ]}


def list_categories(db: Session):
    return {"categories": [
        {"id": c.id, "name": c.category_name}
        for c in db.query(Category).order_by(Category.id).all()
    ]}


def validate_action(db: Session, user: User, action: Action):
    if user.status not in (RoleChoices.seller, RoleChoices.manager):
        raise HTTPException(403, "Недостаточно прав")

    if action.operation == "create_product":
        if set(action.data) != set(ProductCreate.model_fields):
            # is_original has a default, so it may be omitted.
            required = {"product_name", "price", "description", "store_id", "category_id"}
            if not required.issubset(action.data) or not set(action.data).issubset(ProductCreate.model_fields):
                raise HTTPException(422, "Некорректные поля товара")
        data = ProductCreate.model_validate(action.data)
        check_store_permission(db, user, data.store_id)
        if db.get(Category, data.category_id) is None:
            raise HTTPException(404, "Категория не найдена")
        return data.model_dump()

    if set(action.data) != ({"product_id", "changes"} if action.operation == "update_product" else {"product_id"}):
        raise HTTPException(422, "Некорректные поля операции")
    product = get_product_or_404(db, action.data["product_id"])
    check_store_permission(db, user, product.store_id)

    if action.operation == "update_product":
        changes = action.data["changes"]
        if not isinstance(changes, dict) or not changes or not set(changes).issubset(ProductUpdate.model_fields):
            raise HTTPException(422, "Некорректные поля изменения")
        values = ProductUpdate.model_validate(changes).model_dump(exclude_unset=True)
        if any(v is None for v in values.values()):
            raise HTTPException(422, "Поля не могут быть null")
        if "store_id" in values:
            check_store_permission(db, user, values["store_id"])
        if "category_id" in values and db.get(Category, values["category_id"]) is None:
            raise HTTPException(404, "Категория не найдена")
        return values

    if action.operation == "delete_product":
        if db.query(Order).filter(Order.product_id == product.id).first():
            raise HTTPException(409, "Товар связан с заказами")
        return {}

    raise HTTPException(422, "Неизвестная операция")


def execute_action(db: Session, user: User, action: Action):
    try:
        values = validate_action(db, user, action)
        if action.operation == "create_product":
            product = Product(**values)
            db.add(product)
            db.flush()
            db.refresh(product)
            result = {"message": "Товар создан", "items": [product_to_dict(product)]}
        else:
            product = get_product_or_404(db, action.data["product_id"])
            if action.operation == "update_product":
                for field, value in values.items():
                    setattr(product, field, value)
                db.flush()
                db.refresh(product)
                result = {"message": "Товар изменён", "items": [product_to_dict(product)]}
            else:
                product_id = product.id
                db.delete(product)
                db.flush()
                result = {"message": f"Товар ID {product_id} удалён", "items": []}
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


def get_tools(db: Session, user: User):
    @tool
    def list_products_tool():
        """Показывает товары каталога со всеми доступными полями."""
        return search_products(db)

    @tool
    def search_products_tool(query: str):
        """Ищет товары по названию, описанию и категории."""
        return search_products(db, query=query)

    @tool
    def filter_products_tool(
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        store_id: int | None = None,
        category_id: int | None = None,
        product_type: str | None = None,
        is_original: bool | None = None,
        ram_gb: int | None = None,
        color: str | None = None,
        size: str | None = None,
        strict_max: bool = False,
    ):
        """Фильтрует товары. Для 'дешевле' используй strict_max=True; для 'до' — False.
        product_type — произвольное слово из запроса, не список фиксированных видов.
        """
        return search_products(
            db, min_price=min_price, max_price=max_price, store_id=store_id,
            category_id=category_id, product_type=product_type,
            is_original=is_original, ram_gb=ram_gb, color=color,
            size=size, strict_max=strict_max,
        )

    @tool
    def recommend_products_tool(query: str, max_price: Decimal | None = None):
        """Подбирает реальные товары по тексту и бюджету."""
        return search_products(db, query=query, max_price=max_price)

    @tool
    def count_products_tool():
        """Считает количество записей каталога."""
        return count_products(db)

    @tool
    def get_product_tool(product_id: int):
        """Возвращает все доступные данные товара по ID."""
        return get_product(db, product_id)

    @tool
    def compare_products_tool(product_ids: list[int]):
        """Сравнивает 2–5 товаров."""
        return compare_products(db, product_ids)

    @tool
    def list_stores_tool():
        """Список магазинов и доступность редактирования."""
        return list_stores(db, user)

    @tool
    def list_categories_tool():
        """Список категорий и их ID."""
        return list_categories(db)

    tools = [
        list_products_tool, search_products_tool, filter_products_tool,
        recommend_products_tool, count_products_tool, get_product_tool,
        compare_products_tool, list_stores_tool, list_categories_tool,
    ]

    if user.status in (RoleChoices.seller, RoleChoices.manager):
        @tool
        def create_product_tool(data: ProductCreate):
            """Сразу создаёт товар после проверки прав и данных."""
            return execute_action(db, user, Action(operation="create_product", data=data.model_dump(mode="json")))

        @tool
        def update_product_tool(product_id: int, changes: ProductUpdate):
            """Сразу изменяет разрешённый товар."""
            return execute_action(db, user, Action(operation="update_product", data={
                "product_id": product_id,
                "changes": changes.model_dump(mode="json", exclude_unset=True),
            }))

        @tool
        def delete_product_tool(product_id: int):
            """Сразу удаляет свой товар (seller) или любой товар (manager), если нет заказов."""
            return execute_action(db, user, Action(operation="delete_product", data={"product_id": product_id}))

        tools.extend([create_product_tool, update_product_tool, delete_product_tool])

    return tools

"""Add store owner safely after a partially applied migration."""

from alembic import op
import sqlalchemy as sa

revision = "9428a3db1557"
down_revision = "79025e958b7d"
branch_labels = None
depends_on = None

FK_NAME = "fk_store_owner_id_users"
NAMING = {"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"}


def check_sqlite_batch(bind):
    if bind.dialect.name == "sqlite":
        enabled = bind.exec_driver_sql("PRAGMA foreign_keys").scalar()
        if enabled:
            raise RuntimeError(
                "SQLite foreign_keys=ON. Остановлено до изменения таблицы: "
                "нужно настроить batch migration в migrations/env.py."
            )


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"]: column for column in inspector.get_columns("store")}
    foreign_keys = inspector.get_foreign_keys("store")

    owner_column = columns.get("owner_id")
    if owner_column is not None:
        if not isinstance(owner_column["type"], sa.Integer) or not owner_column["nullable"]:
            raise RuntimeError("Существующая колонка owner_id не соответствует модели.")

    owner_fks = [
        fk for fk in foreign_keys
        if "owner_id" in fk["constrained_columns"]
    ]
    has_owner_fk = any(
        fk["constrained_columns"] == ["owner_id"]
        and fk["referred_table"] == "users"
        and fk["referred_columns"] == ["id"]
        for fk in owner_fks
    )
    if owner_fks and not has_owner_fk:
        raise RuntimeError("owner_id уже имеет другую связь. Нужна проверка схемы.")

    if owner_column is not None:
        invalid_owner = bind.execute(sa.text("""
            SELECT s.id
            FROM store AS s
            LEFT JOIN users AS u ON u.id = s.owner_id
            WHERE s.owner_id IS NOT NULL AND u.id IS NULL
            LIMIT 1
        """)).first()
        if invalid_owner:
            raise RuntimeError(
                f"У магазина id={invalid_owner[0]} указан несуществующий owner_id."
            )

    if owner_column is not None and has_owner_fk:
        return

    check_sqlite_batch(bind)

    with op.batch_alter_table("store", naming_convention=NAMING) as batch_op:
        if owner_column is None:
            batch_op.add_column(sa.Column("owner_id", sa.Integer(), nullable=True))
        if not has_owner_fk:
            batch_op.create_foreign_key(FK_NAME, "users", ["owner_id"], ["id"])


def downgrade():
    bind = op.get_bind()
    check_sqlite_batch(bind)

    foreign_keys = sa.inspect(bind).get_foreign_keys("store")
    with op.batch_alter_table("store", naming_convention=NAMING) as batch_op:
        for fk in foreign_keys:
            if fk["constrained_columns"] == ["owner_id"]:
                name = fk["name"] or f"fk_store_owner_id_{fk['referred_table']}"
                batch_op.drop_constraint(name, type_="foreignkey")
        batch_op.drop_column("owner_id")
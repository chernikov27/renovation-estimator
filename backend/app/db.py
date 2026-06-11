from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import get_settings
from backend.app.models import Base, CatalogMetadata, Material, WorkGroup, WorkType
from backend.app.seed import seed_price_list


def _connect_args(database_url: str) -> dict[str, bool]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


settings = get_settings()
engine = create_engine(settings.database_url, connect_args=_connect_args(settings.database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db(target_engine: Engine = engine) -> None:
    migrate_schema(target_engine)
    Base.metadata.create_all(bind=target_engine)
    with Session(target_engine) as session:
        seed_price_list(session, settings.price_list_seed_path)
        session.commit()


def migrate_schema(target_engine: Engine) -> None:
    """Upgrade the local MVP SQLite catalog schema without introducing Alembic."""
    if target_engine.dialect.name != "sqlite":
        return

    inspector = inspect(target_engine)
    table_names = set(inspector.get_table_names())
    if "work_types" not in table_names:
        return

    WorkGroup.__table__.create(bind=target_engine, checkfirst=True)
    CatalogMetadata.__table__.create(bind=target_engine, checkfirst=True)

    work_columns = {column["name"] for column in inspector.get_columns("work_types")}
    with target_engine.connect() as connection:
        work_sql = connection.exec_driver_sql(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='work_types'"
        ).scalar_one_or_none() or ""
        material_sql = connection.exec_driver_sql(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='materials'"
        ).scalar_one_or_none() or ""

        rebuild_work_types = (
            not {"group_code", "sort_order", "quantity_basis", "max_layers", "active"}.issubset(work_columns)
            or "putty', 'primer', 'paint" in work_sql
        )
        rebuild_materials = (
            "materials" in table_names
            and "'u'" not in material_sql
        )

        if rebuild_work_types or rebuild_materials:
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
            connection.exec_driver_sql("PRAGMA legacy_alter_table=ON")

            if "materials" in table_names:
                connection.exec_driver_sql("ALTER TABLE materials RENAME TO materials_legacy")
            connection.exec_driver_sql("ALTER TABLE work_types RENAME TO work_types_legacy")

            WorkType.__table__.create(bind=connection)
            connection.exec_driver_sql(
                """
                INSERT INTO work_types (
                    id, code, name_ru, name_fr, unit, group_code, sort_order,
                    quantity_basis, base_unit_price, default_layers, max_layers, active
                )
                SELECT id, code, name_ru, name_fr, unit, NULL, 0,
                       'area', base_unit_price, default_layers, 5, 1
                FROM work_types_legacy
                """
            )

            if "materials" in table_names:
                Material.__table__.create(bind=connection)
                connection.exec_driver_sql(
                    """
                    INSERT INTO materials (
                        id, work_type_id, name_ru, name_fr, consumption_per_m2,
                        consumption_unit, package_size, package_price
                    )
                    SELECT id, work_type_id, name_ru, name_fr, consumption_per_m2,
                           consumption_unit, package_size, package_price
                    FROM materials_legacy
                    """
                )
                connection.exec_driver_sql("DROP TABLE materials_legacy")

            connection.exec_driver_sql("DROP TABLE work_types_legacy")
            connection.exec_driver_sql("PRAGMA legacy_alter_table=OFF")
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            connection.commit()

    refreshed = inspect(target_engine)
    if "room_works" in refreshed.get_table_names():
        room_work_columns = {column["name"] for column in refreshed.get_columns("room_works")}
        if "quantity" not in room_work_columns:
            with target_engine.begin() as connection:
                connection.exec_driver_sql("ALTER TABLE room_works ADD COLUMN quantity FLOAT")

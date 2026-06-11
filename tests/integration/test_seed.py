from pathlib import Path

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from backend.app import models
from backend.app import db
from backend.app.models import Base, Material, WorkType
from backend.app.seed import seed_price_list


def test_seed_price_list_is_idempotent_and_matches_seed_file(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'app.db'}")
    Base.metadata.create_all(engine)

    seed_path = Path("data/price_list.seed.json")
    with Session(engine) as session:
        seed_price_list(session, seed_path)
        session.commit()
        seed_price_list(session, seed_path)
        session.commit()

        work_types = session.scalars(
            select(WorkType).options(selectinload(WorkType.material)).order_by(WorkType.code)
        ).all()
        materials = session.scalars(select(Material).order_by(Material.name_ru)).all()

    assert [work.code for work in work_types] == ["paint", "primer", "putty"]
    assert len(work_types) == 3
    assert len(materials) == 3

    by_code = {work.code: work for work in work_types}
    assert by_code["putty"].name_ru == "Шпаклёвка стен и потолка"
    assert by_code["putty"].name_fr == "Enduit des murs et plafonds"
    assert by_code["putty"].base_unit_price == 9.5
    assert by_code["putty"].default_layers == 2

    putty_material = by_code["putty"].material
    assert putty_material.name_ru == "Шпаклёвка финишная, мешок 25 кг"
    assert putty_material.consumption_per_m2 == 1.2
    assert putty_material.consumption_unit == "kg"
    assert putty_material.package_size == 25
    assert putty_material.package_price == 14.9


def test_seed_v2_upserts_groups_extended_units_and_catalog_metadata(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'app-v2.db'}")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        seed_price_list(session, Path("data/price_list.seed.json"))
        session.commit()
        seed_price_list(session, Path("data/price_list.seed.v2.json"))
        session.commit()
        seed_price_list(session, Path("data/price_list.seed.v2.json"))
        session.commit()

        work_group = getattr(models, "WorkGroup", None)
        assert work_group is not None
        groups = session.scalars(select(work_group).order_by(work_group.sort_order)).all()
        work_types = session.scalars(
            select(WorkType).options(selectinload(WorkType.material)).order_by(WorkType.code)
        ).all()

    assert [group.code for group in groups] == ["prep", "enduits", "peinture"]
    assert len(work_types) == 9
    by_code = {work.code: work for work in work_types}
    assert by_code["putty"].active == 0
    assert by_code["crack_treatment"].group_code == "prep"
    assert by_code["crack_treatment"].quantity_basis == "length"
    assert by_code["crack_treatment"].unit == "ml"
    assert by_code["sanding"].material.consumption_unit == "u"
    assert by_code["mesh_reinforcement"].material.consumption_unit == "m2"
    assert by_code["paint"].max_layers == 3


def test_migrates_legacy_sqlite_catalog_before_importing_seed_v2(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE work_types (
                    id VARCHAR PRIMARY KEY,
                    code VARCHAR NOT NULL UNIQUE CHECK (code in ('putty', 'primer', 'paint')),
                    name_ru VARCHAR NOT NULL,
                    name_fr VARCHAR NOT NULL,
                    unit VARCHAR NOT NULL,
                    base_unit_price FLOAT NOT NULL,
                    default_layers INTEGER NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE materials (
                    id VARCHAR PRIMARY KEY,
                    work_type_id VARCHAR NOT NULL UNIQUE REFERENCES work_types(id),
                    name_ru VARCHAR NOT NULL,
                    name_fr VARCHAR NOT NULL,
                    consumption_per_m2 FLOAT NOT NULL,
                    consumption_unit VARCHAR NOT NULL CHECK (consumption_unit in ('l', 'kg')),
                    package_size FLOAT NOT NULL,
                    package_price FLOAT NOT NULL
                )
                """
            )
        )

    migrate_schema = getattr(db, "migrate_schema", None)
    assert migrate_schema is not None
    migrate_schema(engine)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        seed_price_list(session, Path("data/price_list.seed.v2.json"))
        session.commit()
        sanding = session.scalar(
            select(WorkType)
            .options(selectinload(WorkType.material))
            .where(WorkType.code == "sanding")
        )

    assert sanding is not None
    assert sanding.material.consumption_unit == "u"

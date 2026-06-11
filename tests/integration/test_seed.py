from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

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

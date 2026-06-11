from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models import Material, WorkType


def seed_price_list(session: Session, seed_path: Path) -> None:
    if session.scalar(select(func.count(WorkType.id))) != 0:
        return

    with seed_path.open("r", encoding="utf-8") as seed_file:
        payload = json.load(seed_file)

    for item in payload["work_types"]:
        material_payload = item["material"]
        work_type = WorkType(
            code=item["code"],
            name_ru=item["name_ru"],
            name_fr=item["name_fr"],
            unit=item.get("unit", "m2"),
            base_unit_price=item["base_unit_price"],
            default_layers=item["default_layers"],
            material=Material(
                name_ru=material_payload["name_ru"],
                name_fr=material_payload["name_fr"],
                consumption_per_m2=material_payload["consumption_per_m2"],
                consumption_unit=material_payload["consumption_unit"],
                package_size=material_payload["package_size"],
                package_price=material_payload["package_price"],
            ),
        )
        session.add(work_type)

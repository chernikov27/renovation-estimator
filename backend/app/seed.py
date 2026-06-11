from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import CatalogMetadata, Material, WorkGroup, WorkType


def seed_price_list(session: Session, seed_path: Path) -> None:
    with seed_path.open("r", encoding="utf-8") as seed_file:
        payload = json.load(seed_file)

    metadata = session.get(CatalogMetadata, 1)
    if metadata is None:
        metadata = CatalogMetadata(id=1)
        session.add(metadata)
    metadata.version = payload.get("version", 1)
    metadata.currency = payload.get("currency", "EUR")
    metadata.vat_presets = payload.get("vat_presets", [])

    for group_payload in payload.get("groups", []):
        group = session.get(WorkGroup, group_payload["code"])
        if group is None:
            group = WorkGroup(code=group_payload["code"])
            session.add(group)
        group.sort_order = group_payload["sort_order"]
        group.name_ru = group_payload["name_ru"]
        group.name_fr = group_payload["name_fr"]

    for item in payload["work_types"]:
        material_payload = item["material"]
        work_type = session.scalar(select(WorkType).where(WorkType.code == item["code"]))
        if work_type is None:
            work_type = WorkType(code=item["code"])
            session.add(work_type)

        work_type.name_ru = item["name_ru"]
        work_type.name_fr = item["name_fr"]
        work_type.unit = item.get("unit", "m2")
        work_type.group_code = item.get("group")
        work_type.sort_order = item.get("sort_order", 0)
        work_type.quantity_basis = item.get("quantity_basis", "area")
        work_type.base_unit_price = item["base_unit_price"]
        work_type.default_layers = item["default_layers"]
        work_type.max_layers = item.get("max_layers", 5)
        work_type.active = 1 if item.get("active", True) else 0

        if work_type.material is None:
            work_type.material = Material()
        work_type.material.name_ru = material_payload["name_ru"]
        work_type.material.name_fr = material_payload["name_fr"]
        work_type.material.consumption_per_m2 = material_payload.get(
            "consumption_per_unit",
            material_payload.get("consumption_per_m2"),
        )
        work_type.material.consumption_unit = material_payload["consumption_unit"]
        work_type.material.package_size = material_payload["package_size"]
        work_type.material.package_price = material_payload["package_price"]

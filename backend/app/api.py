from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.calculation import (
    EstimateCalculationInput,
    OpeningInput,
    RoomCalculationInput,
    WorkCalculationInput,
    calculate_estimate,
)
from backend.app.models import Estimate, Material, Opening, Photo, Room, RoomWork, WorkType
from backend.app.schemas import EstimateCreate, EstimateUpdate, RoomPayload, RoomWorkPayload


router = APIRouter(prefix="/api")

MAX_PHOTO_SIZE_BYTES = 10 * 1024 * 1024
MAX_PHOTOS_PER_ESTIMATE = 10
PHOTO_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def error_payload(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


def not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "not_found", "message": message})


def photo_error(code: str, message: str) -> HTTPException:
    return HTTPException(status_code=422, detail={"code": code, "message": message})


def _estimate_options():
    return (
        selectinload(Estimate.rooms).selectinload(Room.openings),
        selectinload(Estimate.rooms).selectinload(Room.works).selectinload(RoomWork.work_type),
        selectinload(Estimate.rooms)
        .selectinload(Room.works)
        .selectinload(RoomWork.work_type)
        .selectinload(WorkType.material),
        selectinload(Estimate.photos),
    )


def get_estimate_or_404(session: Session, estimate_id: str) -> Estimate:
    estimate = session.scalar(select(Estimate).options(*_estimate_options()).where(Estimate.id == estimate_id))
    if estimate is None:
        raise not_found("Estimate not found")
    return estimate


def get_room_or_404(session: Session, room_id: str) -> Room:
    room = session.scalar(
        select(Room)
        .options(
            selectinload(Room.openings),
            selectinload(Room.works).selectinload(RoomWork.work_type).selectinload(WorkType.material),
        )
        .where(Room.id == room_id)
    )
    if room is None:
        raise not_found("Room not found")
    return room


def get_photo_or_404(session: Session, photo_id: str) -> Photo:
    photo = session.get(Photo, photo_id)
    if photo is None:
        raise not_found("Photo not found")
    return photo


def serialize_estimate(estimate: Estimate) -> dict:
    return {
        "id": estimate.id,
        "title": estimate.title,
        "address": estimate.address,
        "locale": estimate.locale,
        "currency": estimate.currency,
        "vat_pct": estimate.vat_pct,
        "share_token": estimate.share_token,
        "total_amount": estimate.total_amount,
        "created_at": estimate.created_at.isoformat() if estimate.created_at else None,
        "updated_at": estimate.updated_at.isoformat() if estimate.updated_at else None,
        "rooms": [serialize_room(room) for room in estimate.rooms],
        "photos": [serialize_photo(photo) for photo in estimate.photos],
    }


def serialize_room(room: Room) -> dict:
    return {
        "id": room.id,
        "estimate_id": room.estimate_id,
        "name": room.name,
        "length_m": room.length_m,
        "width_m": room.width_m,
        "height_m": room.height_m,
        "include_ceiling": bool(room.include_ceiling),
        "openings": [serialize_opening(opening) for opening in room.openings],
        "works": [serialize_room_work(work) for work in room.works],
    }


def serialize_opening(opening: Opening) -> dict:
    return {
        "id": opening.id,
        "kind": opening.kind,
        "width_m": opening.width_m,
        "height_m": opening.height_m,
        "count": opening.count,
    }


def serialize_room_work(work: RoomWork) -> dict:
    return {
        "id": work.id,
        "work_type_id": work.work_type_id,
        "code": work.work_type.code,
        "name_ru": work.work_type.name_ru,
        "name_fr": work.work_type.name_fr,
        "layers": work.layers,
        "unit_price": work.unit_price,
        "material_consumption_per_m2": work.material_consumption_per_m2,
        "material_consumption_unit": work.work_type.material.consumption_unit,
        "material_package_size": work.material_package_size,
        "material_package_price": work.material_package_price,
        "computed_area": work.computed_area,
        "labor_cost": work.labor_cost,
        "material_cost": work.material_cost,
    }


def serialize_photo(photo) -> dict:
    return {
        "id": photo.id,
        "file_path": photo.file_path,
        "original_name": photo.original_name,
        "mime": photo.mime,
        "size_bytes": photo.size_bytes,
        "created_at": photo.created_at.isoformat() if photo.created_at else None,
    }


def is_valid_magic_bytes(mime: str, content: bytes) -> bool:
    if mime == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")
    if mime == "image/png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if mime == "image/webp":
        return len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    return False


def validate_photo_upload(upload: UploadFile) -> tuple[bytes, str]:
    mime = upload.content_type or ""
    if mime not in PHOTO_EXTENSIONS:
        raise photo_error("invalid_photo_mime", "Unsupported photo MIME type")

    content = upload.file.read(MAX_PHOTO_SIZE_BYTES + 1)
    if len(content) > MAX_PHOTO_SIZE_BYTES:
        raise photo_error("photo_too_large", "Photo exceeds 10 MB")
    if not is_valid_magic_bytes(mime, content):
        raise photo_error("invalid_photo_magic", "Photo content does not match declared MIME type")
    return content, PHOTO_EXTENSIONS[mime]


def serialize_price_list(work_types: list[WorkType]) -> dict:
    return {
        "currency": "EUR",
        "work_types": [
            {
                "id": work_type.id,
                "code": work_type.code,
                "name_ru": work_type.name_ru,
                "name_fr": work_type.name_fr,
                "unit": work_type.unit,
                "base_unit_price": work_type.base_unit_price,
                "default_layers": work_type.default_layers,
                "material": serialize_material(work_type.material),
            }
            for work_type in work_types
        ],
    }


def serialize_material(material: Material) -> dict:
    return {
        "id": material.id,
        "name_ru": material.name_ru,
        "name_fr": material.name_fr,
        "consumption_per_m2": material.consumption_per_m2,
        "consumption_unit": material.consumption_unit,
        "package_size": material.package_size,
        "package_price": material.package_price,
    }


def work_type_by_code(session: Session, code: str) -> WorkType:
    work_type = session.scalar(
        select(WorkType).options(selectinload(WorkType.material)).where(WorkType.code == code)
    )
    if work_type is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "invalid_work_code", "message": f"Unknown work type: {code}"},
        )
    return work_type


def build_room_work(session: Session, payload: RoomWorkPayload) -> RoomWork:
    work_type = work_type_by_code(session, payload.code)
    material = work_type.material
    return RoomWork(
        work_type=work_type,
        layers=payload.layers,
        unit_price=payload.unit_price if payload.unit_price is not None else work_type.base_unit_price,
        material_consumption_per_m2=material.consumption_per_m2,
        material_package_size=material.package_size,
        material_package_price=material.package_price,
    )


def apply_room_payload(session: Session, room: Room, payload: RoomPayload) -> None:
    room.name = payload.name
    room.length_m = payload.length_m
    room.width_m = payload.width_m
    room.height_m = payload.height_m
    room.include_ceiling = 1 if payload.include_ceiling else 0
    room.openings = [
        Opening(kind=opening.kind, width_m=opening.width_m, height_m=opening.height_m, count=opening.count)
        for opening in payload.openings
    ]
    room.works = [build_room_work(session, work) for work in payload.works]


@router.post("/estimates", status_code=status.HTTP_201_CREATED)
def create_estimate(payload: EstimateCreate, request: Request) -> dict:
    with request.app.state.SessionLocal() as session:
        estimate = Estimate(
            title=payload.title,
            address=payload.address,
            locale=payload.locale,
            vat_pct=payload.vat_pct,
        )
        session.add(estimate)
        session.commit()
        return serialize_estimate(get_estimate_or_404(session, estimate.id))


@router.get("/estimates/{estimate_id}")
def read_estimate(estimate_id: str, request: Request) -> dict:
    with request.app.state.SessionLocal() as session:
        return serialize_estimate(get_estimate_or_404(session, estimate_id))


@router.put("/estimates/{estimate_id}")
def update_estimate(estimate_id: str, payload: EstimateUpdate, request: Request) -> dict:
    with request.app.state.SessionLocal() as session:
        estimate = get_estimate_or_404(session, estimate_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(estimate, field, value)
        session.commit()
        return serialize_estimate(get_estimate_or_404(session, estimate_id))


@router.delete("/estimates/{estimate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_estimate(estimate_id: str, request: Request) -> None:
    with request.app.state.SessionLocal() as session:
        estimate = get_estimate_or_404(session, estimate_id)
        session.delete(estimate)
        session.commit()


@router.get("/shared/{share_token}")
def read_shared_estimate(share_token: str, request: Request) -> dict:
    with request.app.state.SessionLocal() as session:
        estimate = session.scalar(select(Estimate).options(*_estimate_options()).where(Estimate.share_token == share_token))
        if estimate is None:
            raise not_found("Estimate not found")
        return serialize_estimate(estimate)


@router.post("/estimates/{estimate_id}/photos", status_code=status.HTTP_201_CREATED)
def upload_estimate_photos(estimate_id: str, request: Request, photos: list[UploadFile] = File(...)) -> dict:
    with request.app.state.SessionLocal() as session:
        estimate = get_estimate_or_404(session, estimate_id)
        if len(estimate.photos) + len(photos) > MAX_PHOTOS_PER_ESTIMATE:
            raise photo_error("too_many_photos", "Estimate cannot have more than 10 photos")

        validated_photos = [(upload, *validate_photo_upload(upload)) for upload in photos]
        upload_dir = Path(request.app.state.uploads_dir) / estimate.id
        upload_dir.mkdir(parents=True, exist_ok=True)

        created_photos: list[Photo] = []
        for upload, content, extension in validated_photos:
            file_path = upload_dir / f"{uuid4()}{extension}"
            file_path.write_bytes(content)
            photo = Photo(
                estimate=estimate,
                file_path=str(file_path),
                original_name=upload.filename or "photo",
                mime=upload.content_type or "",
                size_bytes=len(content),
            )
            session.add(photo)
            created_photos.append(photo)

        session.commit()
        for photo in created_photos:
            session.refresh(photo)
        return {"photos": [serialize_photo(photo) for photo in created_photos]}


@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(photo_id: str, request: Request) -> None:
    with request.app.state.SessionLocal() as session:
        photo = get_photo_or_404(session, photo_id)
        file_path = Path(photo.file_path)
        session.delete(photo)
        session.commit()
        file_path.unlink(missing_ok=True)


@router.post("/estimates/{estimate_id}/rooms", status_code=status.HTTP_201_CREATED)
def create_room(estimate_id: str, payload: RoomPayload, request: Request) -> dict:
    with request.app.state.SessionLocal() as session:
        estimate = get_estimate_or_404(session, estimate_id)
        room = Room(estimate=estimate)
        apply_room_payload(session, room, payload)
        session.add(room)
        session.commit()
        return serialize_room(get_room_or_404(session, room.id))


@router.put("/rooms/{room_id}")
def update_room(room_id: str, payload: RoomPayload, request: Request) -> dict:
    with request.app.state.SessionLocal() as session:
        room = get_room_or_404(session, room_id)
        apply_room_payload(session, room, payload)
        session.commit()
        return serialize_room(get_room_or_404(session, room_id))


@router.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: str, request: Request) -> None:
    with request.app.state.SessionLocal() as session:
        room = get_room_or_404(session, room_id)
        session.delete(room)
        session.commit()


@router.post("/estimates/{estimate_id}/calculate")
def calculate_estimate_endpoint(estimate_id: str, request: Request) -> dict:
    with request.app.state.SessionLocal() as session:
        estimate = get_estimate_or_404(session, estimate_id)
        result = calculate_estimate(to_calculation_input(estimate))
        line_results_by_room = {
            room_result.id: {line.code: line for line in room_result.lines}
            for room_result in result.rooms
        }

        for room in estimate.rooms:
            room_lines = line_results_by_room.get(room.id, {})
            for room_work in room.works:
                line = room_lines.get(room_work.work_type.code)
                if line is None:
                    continue
                room_work.computed_area = float(line.area)
                room_work.labor_cost = float(line.labor_cost)
                room_work.material_cost = float(line.material_cost)

        estimate.total_amount = float(result.total)
        session.commit()
        return serialize_calculation_result(result)


@router.get("/price-list")
def read_price_list(request: Request) -> dict:
    with request.app.state.SessionLocal() as session:
        work_types = session.scalars(
            select(WorkType).options(selectinload(WorkType.material)).order_by(WorkType.code)
        ).all()
        return serialize_price_list(list(work_types))


def to_calculation_input(estimate: Estimate) -> EstimateCalculationInput:
    return EstimateCalculationInput(
        vat_pct=Decimal(str(estimate.vat_pct)),
        rooms=[
            RoomCalculationInput(
                id=room.id,
                name=room.name,
                length_m=Decimal(str(room.length_m)),
                width_m=Decimal(str(room.width_m)),
                height_m=Decimal(str(room.height_m)),
                include_ceiling=bool(room.include_ceiling),
                openings=[
                    OpeningInput(
                        kind=opening.kind,
                        width_m=Decimal(str(opening.width_m)),
                        height_m=Decimal(str(opening.height_m)),
                        count=opening.count,
                    )
                    for opening in room.openings
                ],
                works=[
                    WorkCalculationInput(
                        code=work.work_type.code,
                        layers=work.layers,
                        unit_price=Decimal(str(work.unit_price)),
                        material_consumption_per_m2=Decimal(str(work.material_consumption_per_m2)),
                        material_package_size=Decimal(str(work.material_package_size)),
                        material_package_price=Decimal(str(work.material_package_price)),
                    )
                    for work in room.works
                ],
            )
            for room in estimate.rooms
        ],
    )


def serialize_calculation_result(result) -> dict:
    return {
        "subtotal": float(result.subtotal),
        "vat_pct": float(result.vat_pct),
        "total": float(result.total),
        "warnings": [
            {
                "code": warning.code,
                "message": warning.message,
                "room_id": warning.room_id,
                "room_name": warning.room_name,
            }
            for warning in result.warnings
        ],
        "rooms": [
            {
                "id": room.id,
                "name": room.name,
                "gross_wall_area": float(room.gross_wall_area),
                "openings_area_raw": float(room.openings_area_raw),
                "walls_area": float(room.walls_area),
                "ceiling_area": float(room.ceiling_area),
                "base_area": float(room.base_area),
                "lines": [
                    {
                        "code": line.code,
                        "layers": line.layers,
                        "area": float(line.area),
                        "labor_cost": float(line.labor_cost),
                        "consumption": float(line.consumption),
                        "packages": line.packages,
                        "material_cost": float(line.material_cost),
                        "total_cost": float(line.total_cost),
                    }
                    for line in room.lines
                ],
            }
            for room in result.rooms
        ],
    }

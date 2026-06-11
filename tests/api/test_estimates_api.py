from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.main import create_app
from backend.app.models import Base, Estimate, Photo, RoomWork, WorkType
from backend.app.seed import seed_price_list


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    engine = create_engine(f"sqlite:///{tmp_path / 'api.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with Session(engine) as session:
        seed_price_list(session, Path("data/price_list.seed.json"))
        session.commit()
    app = create_app(testing_session, initialize_database=False)
    app.state.uploads_dir = tmp_path / "uploads"
    return TestClient(app)


@pytest.fixture()
def v2_client(tmp_path: Path) -> TestClient:
    engine = create_engine(f"sqlite:///{tmp_path / 'api-v2.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with Session(engine) as session:
        seed_price_list(session, Path("data/price_list.seed.v2.json"))
        session.commit()
    app = create_app(testing_session, initialize_database=False)
    app.state.uploads_dir = tmp_path / "uploads"
    return TestClient(app)


JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"jpeg-data"
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"png-data"
WEBP_BYTES = b"RIFF\x12\x00\x00\x00WEBPVP8 " + b"webp-data"


def create_estimate(client: TestClient) -> str:
    return client.post("/api/estimates", json={"title": "Estimate"}).json()["id"]


def photo_file(name: str, content: bytes, mime: str) -> tuple[str, tuple[str, bytes, str]]:
    return ("photos", (name, content, mime))


def test_estimate_crud_and_share_view(client: TestClient) -> None:
    created = client.post(
        "/api/estimates",
        json={"title": "Apartment A", "address": "12 rue Test", "locale": "fr"},
    )
    assert created.status_code == 201
    body = created.json()
    estimate_id = body["id"]
    share_token = body["share_token"]
    assert body["title"] == "Apartment A"
    assert body["address"] == "12 rue Test"
    assert body["locale"] == "fr"
    assert body["currency"] == "EUR"
    assert body["vat_pct"] == 20
    assert body["rooms"] == []

    fetched = client.get(f"/api/estimates/{estimate_id}")
    assert fetched.status_code == 200
    assert fetched.json()["share_token"] == share_token

    updated = client.put(
        f"/api/estimates/{estimate_id}",
        json={"title": "Apartment B", "address": None, "locale": "ru", "vat_pct": 10},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Apartment B"
    assert updated.json()["address"] is None
    assert updated.json()["locale"] == "ru"
    assert updated.json()["vat_pct"] == 10

    shared = client.get(f"/api/shared/{share_token}")
    assert shared.status_code == 200
    assert shared.json()["id"] == estimate_id
    assert shared.json()["share_token"] == share_token

    deleted = client.delete(f"/api/estimates/{estimate_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/estimates/{estimate_id}").status_code == 404
    assert client.get(f"/api/shared/{share_token}").status_code == 404


def test_room_create_update_delete_with_openings_and_work_snapshots(client: TestClient) -> None:
    estimate_id = client.post("/api/estimates", json={"title": "Estimate"}).json()["id"]

    created_room = client.post(
        f"/api/estimates/{estimate_id}/rooms",
        json={
            "name": "Salon",
            "length_m": 4,
            "width_m": 3,
            "height_m": 2.7,
            "include_ceiling": True,
            "openings": [
                {"kind": "window", "width_m": 1.5, "height_m": 1.4, "count": 1},
                {"kind": "door", "width_m": 0.9, "height_m": 2.05, "count": 1},
            ],
            "works": [
                {"code": "putty", "layers": 2},
                {"code": "primer", "layers": 1, "unit_price": 3.25},
            ],
        },
    )

    assert created_room.status_code == 201
    room = created_room.json()
    room_id = room["id"]
    assert room["name"] == "Salon"
    assert len(room["openings"]) == 2
    works_by_code = {work["code"]: work for work in room["works"]}
    assert set(works_by_code) == {"putty", "primer"}
    assert works_by_code["putty"]["unit_price"] == 9.5
    assert works_by_code["primer"]["unit_price"] == 3.25
    assert works_by_code["putty"]["material_consumption_unit"] == "kg"
    assert works_by_code["putty"]["material_package_price"] == 14.9

    fetched_estimate = client.get(f"/api/estimates/{estimate_id}").json()
    assert fetched_estimate["rooms"][0]["id"] == room_id

    updated_room = client.put(
        f"/api/rooms/{room_id}",
        json={
            "name": "Bedroom",
            "length_m": 5,
            "width_m": 4,
            "height_m": 2.8,
            "include_ceiling": False,
            "openings": [{"kind": "door", "width_m": 0.8, "height_m": 2, "count": 1}],
            "works": [{"code": "paint", "layers": 2, "unit_price": 8}],
        },
    )
    assert updated_room.status_code == 200
    assert updated_room.json()["name"] == "Bedroom"
    assert updated_room.json()["include_ceiling"] is False
    assert [work["code"] for work in updated_room.json()["works"]] == ["paint"]

    deleted_room = client.delete(f"/api/rooms/{room_id}")
    assert deleted_room.status_code == 204
    assert client.get(f"/api/estimates/{estimate_id}").json()["rooms"] == []


def test_calculate_persists_total_and_computed_room_work_fields(client: TestClient) -> None:
    estimate_id = client.post("/api/estimates", json={"title": "Estimate", "vat_pct": 20}).json()["id"]
    client.post(
        f"/api/estimates/{estimate_id}/rooms",
        json={
            "name": "Control",
            "length_m": 4,
            "width_m": 3,
            "height_m": 2.7,
            "include_ceiling": True,
            "openings": [
                {"kind": "window", "width_m": 1.5, "height_m": 1.4, "count": 1},
                {"kind": "door", "width_m": 0.9, "height_m": 2.05, "count": 1},
            ],
            "works": [
                {"code": "putty", "layers": 2},
                {"code": "primer", "layers": 1},
                {"code": "paint", "layers": 2},
            ],
        },
    )

    calculated = client.post(f"/api/estimates/{estimate_id}/calculate")
    assert calculated.status_code == 200
    result = calculated.json()
    assert result["subtotal"] == 1825.03
    assert result["total"] == 2190.04
    assert result["rooms"][0]["base_area"] == 45.86
    assert result["rooms"][0]["walls_area"] == 33.86
    assert result["rooms"][0]["lines"][0]["area"] == 45.86

    fetched = client.get(f"/api/estimates/{estimate_id}").json()
    assert fetched["total_amount"] == 2190.04
    for room_work in fetched["rooms"][0]["works"]:
        assert room_work["computed_area"] == 45.86
        assert room_work["labor_cost"] is not None
        assert room_work["material_cost"] is not None


def test_price_list_endpoint_is_read_only_and_seeded(client: TestClient) -> None:
    response = client.get("/api/price-list")

    assert response.status_code == 200
    payload = response.json()
    assert payload["currency"] == "EUR"
    assert [item["code"] for item in payload["work_types"]] == ["paint", "primer", "putty"]
    putty = next(item for item in payload["work_types"] if item["code"] == "putty")
    assert putty["name_ru"] == "Шпаклёвка стен и потолка"
    assert putty["material"]["package_size"] == 25


def test_default_price_list_keeps_mvp_frontend_contract(v2_client: TestClient) -> None:
    response = v2_client.get("/api/price-list")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"currency", "work_types"}
    assert [item["code"] for item in payload["work_types"]] == ["paint", "primer", "putty"]
    assert set(payload["work_types"][0]) == {
        "id",
        "code",
        "name_ru",
        "name_fr",
        "unit",
        "base_unit_price",
        "default_layers",
        "material",
    }
    assert set(payload["work_types"][0]["material"]) == {
        "id",
        "name_ru",
        "name_fr",
        "consumption_per_m2",
        "consumption_unit",
        "package_size",
        "package_price",
    }


def test_price_list_version_2_returns_professional_catalog(v2_client: TestClient) -> None:
    response = v2_client.get("/api/price-list?version=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == 2
    assert payload["currency"] == "EUR"
    assert payload["vat_presets"] == [10, 20]
    assert [group["code"] for group in payload["groups"]] == ["prep", "enduits", "peinture"]
    assert len(payload["work_types"]) == 8
    assert "putty" not in {item["code"] for item in payload["work_types"]}

    by_code = {item["code"]: item for item in payload["work_types"]}
    assert by_code["crack_treatment"]["quantity_basis"] == "length"
    assert by_code["crack_treatment"]["unit"] == "ml"
    assert by_code["sanding"]["material"]["consumption_unit"] == "u"
    assert by_code["mesh_reinforcement"]["material"]["consumption_unit"] == "m2"
    assert by_code["paint"]["group"] == "peinture"


def test_length_work_requires_quantity_and_calculates_by_length(v2_client: TestClient) -> None:
    estimate_id = create_estimate(v2_client)
    room_payload = {
        "name": "Salon",
        "length_m": 4,
        "width_m": 3,
        "height_m": 2.7,
        "works": [{"code": "crack_treatment", "layers": 1}],
    }

    missing_quantity = v2_client.post(f"/api/estimates/{estimate_id}/rooms", json=room_payload)
    assert missing_quantity.status_code == 422
    assert missing_quantity.json()["error"]["code"] == "quantity_required"

    room_payload["works"][0]["quantity"] = 6
    created = v2_client.post(f"/api/estimates/{estimate_id}/rooms", json=room_payload)
    assert created.status_code == 201
    assert created.json()["works"][0]["quantity_basis"] == "length"
    assert created.json()["works"][0]["unit"] == "ml"
    assert created.json()["works"][0]["quantity"] == 6

    calculated = v2_client.post(f"/api/estimates/{estimate_id}/calculate")
    assert calculated.status_code == 200
    line = calculated.json()["rooms"][0]["lines"][0]
    assert line["quantity"] == 6
    assert line["unit"] == "ml"
    assert line["labor_cost"] == 36


def test_returns_error_envelope_for_missing_estimate(client: TestClient) -> None:
    response = client.get("/api/estimates/missing")

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Estimate not found"}}


def test_returns_stable_error_code_for_payload_validation(client: TestClient) -> None:
    response = client.post("/api/estimates", json={"title": ""})

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "validation.title.string_too_short",
            "message": "Validation failed",
        }
    }


def test_room_work_price_is_snapshot_not_live_price(client: TestClient) -> None:
    estimate_id = client.post("/api/estimates", json={"title": "Estimate"}).json()["id"]
    room = client.post(
        f"/api/estimates/{estimate_id}/rooms",
        json={
            "length_m": 4,
            "width_m": 3,
            "height_m": 2.7,
            "works": [{"code": "paint", "layers": 2}],
        },
    ).json()
    assert room["works"][0]["unit_price"] == 7.0

    app_session = client.app.state.SessionLocal
    with app_session() as session:
        paint = session.scalar(select(WorkType).where(WorkType.code == "paint"))
        assert paint is not None
        paint.base_unit_price = 99
        session.commit()

    fetched = client.get(f"/api/estimates/{estimate_id}").json()
    assert fetched["rooms"][0]["works"][0]["unit_price"] == 7.0

    with app_session() as session:
        snapshot = session.scalar(select(RoomWork))
        assert snapshot is not None
        assert snapshot.unit_price == 7.0


def test_uploads_jpeg_png_webp_photos_and_deletes_photo(client: TestClient) -> None:
    estimate_id = create_estimate(client)

    uploaded = client.post(
        f"/api/estimates/{estimate_id}/photos",
        files=[
            photo_file("room.jpg", JPEG_BYTES, "image/jpeg"),
            photo_file("wall.png", PNG_BYTES, "image/png"),
            photo_file("ceiling.webp", WEBP_BYTES, "image/webp"),
        ],
    )

    assert uploaded.status_code == 201
    photos = uploaded.json()["photos"]
    assert [photo["original_name"] for photo in photos] == ["room.jpg", "wall.png", "ceiling.webp"]
    assert [photo["mime"] for photo in photos] == ["image/jpeg", "image/png", "image/webp"]
    for photo in photos:
        file_path = Path(photo["file_path"])
        assert file_path.exists()
        assert file_path.parent.name == estimate_id

    fetched = client.get(f"/api/estimates/{estimate_id}")
    assert len(fetched.json()["photos"]) == 3

    deleted = client.delete(f"/api/photos/{photos[0]['id']}")

    assert deleted.status_code == 204
    assert not Path(photos[0]["file_path"]).exists()
    assert len(client.get(f"/api/estimates/{estimate_id}").json()["photos"]) == 2

    app_session = client.app.state.SessionLocal
    with app_session() as session:
        assert session.get(Photo, photos[0]["id"]) is None


def test_rejects_photo_over_10_mb(client: TestClient) -> None:
    estimate_id = create_estimate(client)
    too_large = JPEG_BYTES + b"x" * (10 * 1024 * 1024)

    response = client.post(
        f"/api/estimates/{estimate_id}/photos",
        files=[photo_file("large.jpg", too_large, "image/jpeg")],
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "photo_too_large"


def test_rejects_photo_with_invalid_mime_or_magic_bytes(client: TestClient) -> None:
    estimate_id = create_estimate(client)

    invalid_mime = client.post(
        f"/api/estimates/{estimate_id}/photos",
        files=[photo_file("room.txt", JPEG_BYTES, "text/plain")],
    )
    invalid_magic = client.post(
        f"/api/estimates/{estimate_id}/photos",
        files=[photo_file("room.png", JPEG_BYTES, "image/png")],
    )

    assert invalid_mime.status_code == 422
    assert invalid_mime.json()["error"]["code"] == "invalid_photo_mime"
    assert invalid_magic.status_code == 422
    assert invalid_magic.json()["error"]["code"] == "invalid_photo_magic"


def test_rejects_more_than_10_photos_per_estimate(client: TestClient) -> None:
    estimate_id = create_estimate(client)

    first_batch = client.post(
        f"/api/estimates/{estimate_id}/photos",
        files=[photo_file(f"room-{index}.jpg", JPEG_BYTES, "image/jpeg") for index in range(10)],
    )
    overflow = client.post(
        f"/api/estimates/{estimate_id}/photos",
        files=[photo_file("room-11.jpg", JPEG_BYTES, "image/jpeg")],
    )

    assert first_batch.status_code == 201
    assert len(first_batch.json()["photos"]) == 10
    assert overflow.status_code == 422
    assert overflow.json()["error"]["code"] == "too_many_photos"

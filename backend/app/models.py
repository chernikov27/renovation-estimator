from __future__ import annotations

import secrets
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def uuid4_str() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def share_token() -> str:
    return secrets.token_urlsafe(16)


class Base(DeclarativeBase):
    pass


class Estimate(Base):
    __tablename__ = "estimates"
    __table_args__ = (CheckConstraint("locale in ('ru', 'fr')", name="ck_estimates_locale"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid4_str)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str | None] = mapped_column(String(250))
    locale: Mapped[str] = mapped_column(String(2), default="ru", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    vat_pct: Mapped[float] = mapped_column(Float, default=20, nullable=False)
    share_token: Mapped[str] = mapped_column(String, unique=True, nullable=False, default=share_token)
    total_amount: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    rooms: Mapped[list[Room]] = relationship(back_populates="estimate", cascade="all, delete-orphan")
    photos: Mapped[list[Photo]] = relationship(back_populates="estimate", cascade="all, delete-orphan")


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid4_str)
    estimate_id: Mapped[str] = mapped_column(ForeignKey("estimates.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    length_m: Mapped[float] = mapped_column(Float, nullable=False)
    width_m: Mapped[float] = mapped_column(Float, nullable=False)
    height_m: Mapped[float] = mapped_column(Float, nullable=False)
    include_ceiling: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    estimate: Mapped[Estimate] = relationship(back_populates="rooms")
    openings: Mapped[list[Opening]] = relationship(back_populates="room", cascade="all, delete-orphan")
    works: Mapped[list[RoomWork]] = relationship(back_populates="room", cascade="all, delete-orphan")


class Opening(Base):
    __tablename__ = "openings"
    __table_args__ = (CheckConstraint("kind in ('window', 'door')", name="ck_openings_kind"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid4_str)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    width_m: Mapped[float] = mapped_column(Float, nullable=False)
    height_m: Mapped[float] = mapped_column(Float, nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    room: Mapped[Room] = relationship(back_populates="openings")


class WorkType(Base):
    __tablename__ = "work_types"
    __table_args__ = (CheckConstraint("code in ('putty', 'primer', 'paint')", name="ck_work_types_code"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid4_str)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name_ru: Mapped[str] = mapped_column(String, nullable=False)
    name_fr: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str] = mapped_column(String, default="m2", nullable=False)
    base_unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    default_layers: Mapped[int] = mapped_column(Integer, nullable=False)

    material: Mapped[Material] = relationship(
        back_populates="work_type",
        cascade="all, delete-orphan",
        uselist=False,
    )
    room_works: Mapped[list[RoomWork]] = relationship(back_populates="work_type")


class Material(Base):
    __tablename__ = "materials"
    __table_args__ = (CheckConstraint("consumption_unit in ('l', 'kg')", name="ck_materials_unit"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid4_str)
    work_type_id: Mapped[str] = mapped_column(ForeignKey("work_types.id"), unique=True, nullable=False)
    name_ru: Mapped[str] = mapped_column(String, nullable=False)
    name_fr: Mapped[str] = mapped_column(String, nullable=False)
    consumption_per_m2: Mapped[float] = mapped_column(Float, nullable=False)
    consumption_unit: Mapped[str] = mapped_column(String, nullable=False)
    package_size: Mapped[float] = mapped_column(Float, nullable=False)
    package_price: Mapped[float] = mapped_column(Float, nullable=False)

    work_type: Mapped[WorkType] = relationship(back_populates="material")


class RoomWork(Base):
    __tablename__ = "room_works"
    __table_args__ = (UniqueConstraint("room_id", "work_type_id", name="uq_room_works_room_work_type"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid4_str)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    work_type_id: Mapped[str] = mapped_column(ForeignKey("work_types.id"), nullable=False)
    layers: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    material_consumption_per_m2: Mapped[float] = mapped_column(Float, nullable=False)
    material_package_size: Mapped[float] = mapped_column(Float, nullable=False)
    material_package_price: Mapped[float] = mapped_column(Float, nullable=False)
    computed_area: Mapped[float | None] = mapped_column(Float)
    labor_cost: Mapped[float | None] = mapped_column(Float)
    material_cost: Mapped[float | None] = mapped_column(Float)

    room: Mapped[Room] = relationship(back_populates="works")
    work_type: Mapped[WorkType] = relationship(back_populates="room_works")


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid4_str)
    estimate_id: Mapped[str] = mapped_column(ForeignKey("estimates.id", ondelete="CASCADE"), nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    original_name: Mapped[str] = mapped_column(String, nullable=False)
    mime: Mapped[str] = mapped_column(String, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    estimate: Mapped[Estimate] = relationship(back_populates="photos")

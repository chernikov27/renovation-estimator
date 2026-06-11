from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP


AREA_QUANT = Decimal("0.01")
MONEY_QUANT = Decimal("0.01")


def _decimal(value: Decimal | int | float | str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _round_area(value: Decimal) -> Decimal:
    return value.quantize(AREA_QUANT, rounding=ROUND_HALF_UP)


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def _ceil_decimal(value: Decimal) -> int:
    if value <= 0:
        return 0
    return int(value.to_integral_value(rounding=ROUND_CEILING))


@dataclass(slots=True)
class OpeningInput:
    kind: str
    width_m: Decimal
    height_m: Decimal
    count: int = 1


@dataclass(slots=True)
class WorkCalculationInput:
    code: str
    layers: int
    unit_price: Decimal
    material_consumption_per_m2: Decimal
    material_package_size: Decimal
    material_package_price: Decimal


@dataclass(slots=True)
class RoomCalculationInput:
    length_m: Decimal
    width_m: Decimal
    height_m: Decimal
    id: str | None = None
    name: str = ""
    include_ceiling: bool = True
    openings: list[OpeningInput] = field(default_factory=list)
    works: list[WorkCalculationInput] = field(default_factory=list)


@dataclass(slots=True)
class EstimateCalculationInput:
    rooms: list[RoomCalculationInput]
    vat_pct: Decimal = Decimal("20")


@dataclass(frozen=True, slots=True)
class CalculationWarning:
    code: str
    message: str
    room_id: str | None = None
    room_name: str = ""


@dataclass(frozen=True, slots=True)
class WorkCalculationResult:
    code: str
    layers: int
    area: Decimal
    labor_cost: Decimal
    consumption: Decimal
    packages: int
    material_cost: Decimal
    total_cost: Decimal


@dataclass(frozen=True, slots=True)
class RoomCalculationResult:
    id: str | None
    name: str
    gross_wall_area: Decimal
    openings_area_raw: Decimal
    walls_area: Decimal
    ceiling_area: Decimal
    base_area: Decimal
    lines: list[WorkCalculationResult]


@dataclass(frozen=True, slots=True)
class EstimateCalculationResult:
    rooms: list[RoomCalculationResult]
    subtotal: Decimal
    vat_pct: Decimal
    total: Decimal
    warnings: list[CalculationWarning]


def calculate_estimate(estimate: EstimateCalculationInput) -> EstimateCalculationResult:
    warnings: list[CalculationWarning] = []
    room_results: list[RoomCalculationResult] = []
    subtotal = Decimal("0")

    for room in estimate.rooms:
        room_result = _calculate_room(room, warnings)
        room_results.append(room_result)
        subtotal += sum((line.total_cost for line in room_result.lines), Decimal("0"))

    rounded_subtotal = _round_money(subtotal)
    vat_pct = _decimal(estimate.vat_pct)
    total = _round_money(rounded_subtotal * (Decimal("1") + vat_pct / Decimal("100")))

    return EstimateCalculationResult(
        rooms=room_results,
        subtotal=rounded_subtotal,
        vat_pct=vat_pct,
        total=total,
        warnings=warnings,
    )


def _calculate_room(
    room: RoomCalculationInput,
    warnings: list[CalculationWarning],
) -> RoomCalculationResult:
    length = _decimal(room.length_m)
    width = _decimal(room.width_m)
    height = _decimal(room.height_m)

    perimeter = Decimal("2") * (length + width)
    gross_wall_area_raw = perimeter * height
    openings_area_raw = sum(
        _decimal(opening.width_m) * _decimal(opening.height_m) * opening.count
        for opening in room.openings
    )

    if openings_area_raw > gross_wall_area_raw:
        walls_area_raw = Decimal("0")
        warnings.append(
            CalculationWarning(
                code="openings_exceed_wall_area",
                message="Openings area exceeds gross wall area; wall area was clamped to zero.",
                room_id=room.id,
                room_name=room.name,
            )
        )
    else:
        walls_area_raw = gross_wall_area_raw - openings_area_raw

    ceiling_area_raw = length * width if room.include_ceiling else Decimal("0")
    base_area = _round_area(walls_area_raw + ceiling_area_raw)

    lines = [_calculate_work(base_area, work) for work in room.works]

    return RoomCalculationResult(
        id=room.id,
        name=room.name,
        gross_wall_area=_round_area(gross_wall_area_raw),
        openings_area_raw=openings_area_raw,
        walls_area=_round_area(walls_area_raw),
        ceiling_area=_round_area(ceiling_area_raw),
        base_area=base_area,
        lines=lines,
    )


def _calculate_work(area: Decimal, work: WorkCalculationInput) -> WorkCalculationResult:
    if work.layers < 1:
        raise ValueError("layers must be greater than zero")

    package_size = _decimal(work.material_package_size)
    if package_size <= 0:
        raise ValueError("material_package_size must be greater than zero")

    layers = Decimal(work.layers)
    labor_cost = _round_money(area * _decimal(work.unit_price) * layers)
    raw_consumption = area * _decimal(work.material_consumption_per_m2) * layers
    packages = _ceil_decimal(raw_consumption / package_size)
    material_cost = _round_money(Decimal(packages) * _decimal(work.material_package_price))
    total_cost = _round_money(labor_cost + material_cost)

    return WorkCalculationResult(
        code=work.code,
        layers=work.layers,
        area=area,
        labor_cost=labor_cost,
        consumption=_round_area(raw_consumption),
        packages=packages,
        material_cost=material_cost,
        total_cost=total_cost,
    )

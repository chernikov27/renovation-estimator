from decimal import Decimal

from backend.app.calculation import (
    EstimateCalculationInput,
    OpeningInput,
    RoomCalculationInput,
    WorkCalculationInput,
    calculate_estimate,
)


def work(
    code: str = "paint",
    layers: int = 1,
    unit_price: str = "1",
    consumption_per_m2: str = "0",
    package_size: str = "1",
    package_price: str = "0",
) -> WorkCalculationInput:
    return WorkCalculationInput(
        code=code,
        layers=layers,
        unit_price=Decimal(unit_price),
        material_consumption_per_m2=Decimal(consumption_per_m2),
        material_package_size=Decimal(package_size),
        material_package_price=Decimal(package_price),
    )


def test_control_room_area_and_seeded_work_totals() -> None:
    result = calculate_estimate(
        EstimateCalculationInput(
            vat_pct=Decimal("20"),
            rooms=[
                RoomCalculationInput(
                    id="room-1",
                    name="Room 1",
                    length_m=Decimal("4"),
                    width_m=Decimal("3"),
                    height_m=Decimal("2.7"),
                    openings=[
                        OpeningInput(kind="window", width_m=Decimal("1.5"), height_m=Decimal("1.4")),
                        OpeningInput(kind="door", width_m=Decimal("0.9"), height_m=Decimal("2.05")),
                    ],
                    works=[
                        work("putty", 2, "9.5", "1.2", "25", "14.9"),
                        work("primer", 1, "2.5", "0.12", "10", "24.5"),
                        work("paint", 2, "7.0", "0.15", "10", "49.0"),
                    ],
                )
            ],
        )
    )

    room = result.rooms[0]
    assert room.openings_area_raw == Decimal("3.945")
    assert room.walls_area == Decimal("33.86")
    assert room.ceiling_area == Decimal("12.00")
    assert room.base_area == Decimal("45.86")

    lines = {line.code: line for line in room.lines}
    assert lines["putty"].labor_cost == Decimal("871.34")
    assert lines["putty"].consumption == Decimal("110.06")
    assert lines["putty"].packages == 5
    assert lines["putty"].material_cost == Decimal("74.50")
    assert lines["putty"].total_cost == Decimal("945.84")

    assert lines["primer"].labor_cost == Decimal("114.65")
    assert lines["primer"].consumption == Decimal("5.50")
    assert lines["primer"].packages == 1
    assert lines["primer"].material_cost == Decimal("24.50")
    assert lines["primer"].total_cost == Decimal("139.15")

    assert lines["paint"].labor_cost == Decimal("642.04")
    assert lines["paint"].consumption == Decimal("13.76")
    assert lines["paint"].packages == 2
    assert lines["paint"].material_cost == Decimal("98.00")
    assert lines["paint"].total_cost == Decimal("740.04")

    assert result.subtotal == Decimal("1825.03")
    assert result.total == Decimal("2190.04")


def test_openings_larger_than_walls_clamp_wall_area_and_warn() -> None:
    result = calculate_estimate(
        EstimateCalculationInput(
            rooms=[
                RoomCalculationInput(
                    id="small-room",
                    name="Small room",
                    length_m=Decimal("2"),
                    width_m=Decimal("2"),
                    height_m=Decimal("2"),
                    openings=[
                        OpeningInput(
                            kind="window",
                            width_m=Decimal("5"),
                            height_m=Decimal("3"),
                            count=2,
                        )
                    ],
                    works=[work()],
                )
            ],
        )
    )

    assert result.rooms[0].walls_area == Decimal("0.00")
    assert result.rooms[0].base_area == Decimal("4.00")
    assert result.warnings[0].code == "openings_exceed_wall_area"
    assert result.warnings[0].room_id == "small-room"


def test_excludes_ceiling_when_include_ceiling_is_false() -> None:
    result = calculate_estimate(
        EstimateCalculationInput(
            rooms=[
                RoomCalculationInput(
                    length_m=Decimal("4"),
                    width_m=Decimal("3"),
                    height_m=Decimal("2.7"),
                    include_ceiling=False,
                    works=[work()],
                )
            ],
        )
    )

    assert result.rooms[0].walls_area == Decimal("37.80")
    assert result.rooms[0].ceiling_area == Decimal("0.00")
    assert result.rooms[0].base_area == Decimal("37.80")


def test_packages_use_ceil_and_money_uses_half_up_rounding() -> None:
    result = calculate_estimate(
        EstimateCalculationInput(
            rooms=[
                RoomCalculationInput(
                    length_m=Decimal("0.5"),
                    width_m=Decimal("0.5"),
                    height_m=Decimal("1.5"),
                    include_ceiling=False,
                    works=[
                        work(
                            code="rounding",
                            unit_price="0.335",
                            consumption_per_m2="0.34",
                            package_size="1",
                            package_price="2.005",
                        )
                    ],
                )
            ],
        )
    )

    line = result.rooms[0].lines[0]
    assert result.rooms[0].base_area == Decimal("3.00")
    assert line.labor_cost == Decimal("1.01")
    assert line.consumption == Decimal("1.02")
    assert line.packages == 2
    assert line.material_cost == Decimal("4.01")
    assert line.total_cost == Decimal("5.02")


def test_multiple_rooms_sum_subtotal_and_apply_vat() -> None:
    result = calculate_estimate(
        EstimateCalculationInput(
            vat_pct=Decimal("10"),
            rooms=[
                RoomCalculationInput(
                    length_m=Decimal("0.5"),
                    width_m=Decimal("0.5"),
                    height_m=Decimal("1.5"),
                    include_ceiling=False,
                    works=[work(unit_price="2")],
                ),
                RoomCalculationInput(
                    length_m=Decimal("0.5"),
                    width_m=Decimal("1"),
                    height_m=Decimal("1.5"),
                    include_ceiling=False,
                    works=[work(unit_price="2")],
                ),
            ],
        )
    )

    assert [room.base_area for room in result.rooms] == [Decimal("3.00"), Decimal("4.50")]
    assert result.subtotal == Decimal("15.00")
    assert result.total == Decimal("16.50")

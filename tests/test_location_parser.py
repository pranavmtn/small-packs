"""Lightweight tests for the location parser (no DB required)."""

from app.services.location_parser import parse_location


def test_roof_top_storage():
    assert parse_location("Roof Top Storage first box first level") == [
        "Roof Top Storage",
        "First Box",
        "First Level",
    ]


def test_kitchen_cupboard():
    assert parse_location("Kitchen cupboard top shelf") == [
        "Kitchen",
        "Cupboard",
        "Top Shelf",
    ]


def test_explicit_separators():
    assert parse_location("Garage > Left Shelf > Bin 2") == [
        "Garage",
        "Left Shelf",
        "Bin 2",
    ]


def test_empty():
    assert parse_location("") == []
    assert parse_location("   ") == []

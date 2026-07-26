from datetime import date

import pytest
from fastapi import HTTPException

from app.main import hash_password, mock_inventory, validate_dates, verify_password


def test_password_hash_is_salted_and_verifiable():
    first = hash_password("A-strong-password")
    second = hash_password("A-strong-password")
    assert first != second
    assert verify_password("A-strong-password", first)
    assert not verify_password("wrong-password", first)


@pytest.mark.parametrize("service", ["flight", "hotel", "bus", "cab", "event", "package"])
def test_mock_inventory_normalizes_every_service(service):
    offers = mock_inventory(service, "Coimbatore", "Bengaluru", 2)
    assert len(offers) == 3
    assert all(offer["currency"] == "INR" for offer in offers)
    assert all(offer["price"] > 0 for offer in offers)
    assert offers[0]["price"] < offers[-1]["price"]


def test_date_validation_accepts_same_day_and_rejects_reverse_range():
    validate_dates(date(2026, 8, 1), date(2026, 8, 1))
    with pytest.raises(HTTPException) as error:
        validate_dates(date(2026, 8, 2), date(2026, 8, 1))
    assert error.value.status_code == 422

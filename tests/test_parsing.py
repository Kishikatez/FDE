"""Tests for the no-key receipt parser."""

from datetime import date

import pytest

from app.services.parsing import ReceiptParseError, parse_fallback


TODAY = date(2026, 9, 19)


def test_parses_messy_seed_receipt():
    parsed = parse_fallback("Meru Cabs PVT LTD Trip 4471 12/09/2026 Rs.214.00 Thank you", today=TODAY)
    assert parsed.merchant == "Meru Cabs PVT LTD Trip 4471"
    assert parsed.amount_paise == 21400
    assert parsed.expense_date == date(2026, 9, 12)
    assert parsed.category.value == "Taxi"


def test_parses_rupees_suffix_and_invoice():
    parsed = parse_fallback("amazon order printer paper + stapler 468 rupees inv IN-88213 14/09/2026", today=TODAY)
    assert parsed.amount_paise == 46800
    assert parsed.receipt_no == "IN-88213"
    assert parsed.category.value == "Supplies"


def test_rejects_future_and_old_dates():
    with pytest.raises(ReceiptParseError, match="future"):
        parse_fallback("Taxi Rs 214 20/09/2026", today=TODAY)
    with pytest.raises(ReceiptParseError, match="outside"):
        parse_fallback("Taxi Rs 214 01/01/2026", today=TODAY)


def test_rejects_non_positive_amount():
    with pytest.raises(ReceiptParseError, match="greater than zero"):
        parse_fallback("Taxi Rs 0 12/09/2026", today=TODAY)
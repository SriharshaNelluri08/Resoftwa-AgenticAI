import pytest
from server import check_po_receipt, get_po

def test_get_existing_po():
    po = get_po("4500014")
    assert po["po_number"] == "4500014"

def test_valid_receipt_check():
    result = check_po_receipt("4500014", 20)
    assert result["status"] == "success"
    assert result["new_deliveredQty"] == 20

def test_over_receipt_check():
    result = check_po_receipt("4500014", 100)
    assert result["status"] == "error"
    assert result["message"] == "Received quantity exceeds ordered quantity"

def test_zero_quantity_check():
    result = check_po_receipt("4500014", 0)
    assert result["status"] == "error"
    assert result["message"] == "Quantity must be greater than 0"
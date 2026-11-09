from pathlib import Path
import csv
from datetime import datetime
from mcp.server import MCPServer

mcp = MCPServer("po-tools")

# Point to our csv file
DATA = Path(__file__).parent / "po_list.csv"

@mcp.tool()
def get_po(po_number: str) -> dict:
    """Return one purchase order by its PO number."""
    try:
        with open(DATA, mode="r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["po_number"] == po_number:
                    return row
    except Exception as e:
        return {"error": str(e)}
    
    # Break it on purpose / handle clean error for bad PO number!
    return {"error": f"Oopsie! PO {po_number} not found in our records."}

@mcp.tool()
def list_late_pos(today: str) -> list:
    """List all purchase orders that are late compared to today's date (YYYY-MM-DD)."""
    late_pos = []
    try:
        today_date = datetime.strptime(today, "%Y-%m-%d")
        with open(DATA, mode="r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                delivery_date = datetime.strptime(row["delivery_date"], "%Y-%m-%d")
                if delivery_date < today_date or row["status"].lower() == "late":
                    late_pos.append(row)
    except Exception as e:
        return [{"error": str(e)}]
    
    return late_pos

if __name__ == "__main__":
    mcp.run(transport="stdio")
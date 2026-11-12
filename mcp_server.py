"""Optional: expose the three skills as MCP tools (Path B).
Install:  pip install mcp      Run:  python mcp_server.py
NOTE: written to the official Python SDK (FastMCP); not run in my offline sandbox."""
from mcp.server.fastmcp import FastMCP
import tools

mcp = FastMCP("requisition-agent")

@mcp.tool()
def check_supplier(supplier: str) -> dict:
    """Return supplier status: good / new / poor / unknown."""
    return tools.check_supplier(supplier)

@mcp.tool()
def create_po(req_id: str, supplier: str, amount: int) -> dict:
    """Create a PO in po_created.json (sandbox only, never a real system)."""
    return tools.create_po(req_id, supplier, amount)

@mcp.tool()
def route_to_manager(req_id: str, supplier: str, amount: int, reason: str) -> dict:
    """Send the requisition to the procurement manager with a reason."""
    return tools.route_to_manager(req_id, supplier, amount, reason)

if __name__ == "__main__":
    mcp.run()

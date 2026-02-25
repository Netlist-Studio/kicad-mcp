from mcp.server.fastmcp import FastMCP

from kicad_mcp.connection import get_kicad


def register_tools(mcp: FastMCP) -> None:

    @mcp.tool()
    def ping() -> str:
        """Check if KiCad is running and accessible via the IPC API."""
        try:
            kicad = get_kicad()
            kicad.ping()
            return "KiCad is running and accessible."
        except Exception as exc:
            return f"KiCad is not accessible: {exc}"

    @mcp.tool()
    def get_version() -> str:
        """Get the version string of the running KiCad instance."""
        try:
            kicad = get_kicad()
            version = kicad.get_version()
            return str(version)
        except Exception as exc:
            return f"Failed to get KiCad version: {exc}"

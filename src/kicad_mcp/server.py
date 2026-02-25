import sys
from pathlib import Path

# When loaded directly by `mcp dev`, relative imports break because the file
# is not imported as part of a package. Ensure src/ is on sys.path so that
# absolute imports work in both execution modes.
_src = Path(__file__).parent.parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from mcp.server.fastmcp import FastMCP

from kicad_mcp.tools.info import register_tools as register_info
from kicad_mcp.tools.board import register_tools as register_board

mcp = FastMCP(
    "kicad",
    instructions=(
        "Interact with a running KiCad 9 instance via its IPC API. "
        "All spatial positions are in millimetres. "
        "KiCad must be open with the API server enabled "
        "(Preferences > Plugins > KiCad API Server)."
    ),
)

register_info(mcp)
register_board(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

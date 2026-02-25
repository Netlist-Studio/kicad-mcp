# kicad-mcp

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An MCP server for controlling KiCad 9 over its IPC API from Claude Code.

## Requirements

- KiCad 9 with the API server enabled (Preferences > Plugins > KiCad API Server)
- Python >= 3.10
- [uv](https://github.com/astral-sh/uv)

## Install

```bash
git clone https://github.com/your-org/kicad-mcp
cd kicad-mcp
uv sync
```

Add to Claude Code:

```bash
claude mcp add kicad -- uv --directory /path/to/kicad-mcp run kicad-mcp
```

Or add to `.claude/settings.json` manually:

```json
"kicad": {
  "command": "uv",
  "args": ["--directory", "/path/to/kicad-mcp", "run", "kicad-mcp"]
}
```

Open a `.kicad_pcb` file in KiCad, then test your connection:

```bash
uv run kicad-mcp
```

## How it works

The server connects to KiCad's local UNIX socket (`/tmp/kicad/api.sock`) using the `kicad-python` bindings. It exposes board data and edit operations as MCP tools, allowing Claude to read the board state and make changes that appear instantly in the KiCad editor with full undo support.

All positions are in millimetres. Write operations are wrapped in a commit so they appear as a single undo step.

## Available tools

| Tool | Description |
|---|---|
| `ping` | Check KiCad is running and accessible |
| `get_version` | Get the KiCad version string |
| `get_board_info` | Summary counts of footprints, tracks, vias, nets, zones |
| `get_footprints` | List footprints with position, layer and value; supports reference filter |
| `get_nets` | List all nets by name and code |
| `get_tracks` | List all copper track segments |
| `get_vias` | List all vias |
| `get_zones` | List all copper zones |
| `get_board_outline` | Return the Edge.Cuts geometry |
| `get_component_connections` | Show which nets each component is on and which other components share them |
| `move_footprint` | Move a footprint to an absolute position |
| `rotate_footprint` | Set the absolute rotation of a footprint in degrees |
| `batch_move_footprints` | Move up to ~5 footprints in a single undo step |
| `create_track` | Add a copper track segment to a named net |
| `remove_items_by_id` | Remove board items by KiCad item ID |
| `refill_zones` | Refill all copper zones |
| `save_board` | Save the board to disk |

## Example usage

Once added to Claude Code, describe what you want in natural language:

> *"Move all components inside the board outline and group passives next to the chips they connect to."*

> *"Route the crystal load caps C3 and C4 to Y1."*

> *"Show me everything connected to U1."*

> *"Refill zones and save the board."*

---

*Built with [Claude Code](https://claude.ai/claude-code)*

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from kicad_mcp.connection import get_kicad


# ---------------------------------------------------------------------------
# Unit conversion helpers
# ---------------------------------------------------------------------------

def _nm_to_mm(nm: int) -> float:
    return nm / 1_000_000


def _mm_to_nm(mm: float) -> int:
    return int(mm * 1_000_000)


def _pos_to_dict(pos: Any) -> dict[str, float]:
    return {"x_mm": _nm_to_mm(pos.x), "y_mm": _nm_to_mm(pos.y)}


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

def register_tools(mcp: FastMCP) -> None:

    # ------------------------------------------------------------------
    # Read tools
    # ------------------------------------------------------------------

    @mcp.tool()
    def get_board_info() -> dict[str, Any]:
        """Return summary counts for the open PCB board."""
        try:
            board = get_kicad().get_board()
            footprints = board.get_footprints()
            tracks = board.get_tracks()
            nets = board.get_nets()
            zones = board.get_zones()

            vias = [t for t in tracks if _is_via(t)]
            plain_tracks = [t for t in tracks if not _is_via(t)]

            return {
                "footprints": len(footprints),
                "tracks": len(plain_tracks),
                "vias": len(vias),
                "nets": len(nets),
                "zones": len(zones),
            }
        except Exception as exc:
            return {"error": str(exc)}

    @mcp.tool()
    def debug_footprint_attrs() -> list[str]:
        """Return attribute names on the first FootprintInstance for debugging."""
        try:
            board = get_kicad().get_board()
            footprints = board.get_footprints()
            if not footprints:
                return ["no footprints found"]
            fp = footprints[0]
            return [a for a in dir(fp) if not a.startswith("__")]
        except Exception as exc:
            return [f"error: {exc}"]

    @mcp.tool()
    def debug_board_methods() -> list[str]:
        """Return method/attribute names on the Board object for debugging."""
        try:
            board = get_kicad().get_board()
            return [a for a in dir(board) if not a.startswith("__")]
        except Exception as exc:
            return [f"error: {exc}"]

    @mcp.tool()
    def debug_reference_field() -> dict[str, Any]:
        """Inspect the reference_field structure to find the correct access path."""
        try:
            board = get_kicad().get_board()
            footprints = board.get_footprints()
            if not footprints:
                return {"error": "no footprints"}
            fp = footprints[0]
            rf = fp.reference_field
            return {
                "type": type(rf).__name__,
                "attrs": [a for a in dir(rf) if not a.startswith("__")],
                "str": str(rf),
                "text_attrs": [a for a in dir(rf.text) if not a.startswith("__")] if hasattr(rf, "text") else [],
                "text_value": str(rf.text.value) if hasattr(rf, "text") and hasattr(rf.text, "value") else "n/a",
            }
        except Exception as exc:
            return {"error": str(exc)}

    @mcp.tool()
    def get_footprints(reference_filter: str = "") -> list[dict[str, Any]]:
        """
        List footprints on the open board.

        Args:
            reference_filter: Optional substring filter applied to the
                              reference designator (case-insensitive).
        """
        try:
            board = get_kicad().get_board()
            footprints = board.get_footprints()
            result = []
            for fp in footprints:
                try:
                    ref = str(fp.reference_field.text.value)
                except Exception:
                    ref = str(fp.reference_field)
                if reference_filter and reference_filter.lower() not in ref.lower():
                    continue
                try:
                    pos = _pos_to_dict(fp.position)
                except Exception:
                    pos = {}
                try:
                    layer = str(fp.layer)
                except Exception:
                    layer = "unknown"
                try:
                    value = str(fp.value_field.text.value)
                except Exception:
                    value = ""
                result.append({
                    "reference": ref,
                    "value": value,
                    "position_mm": pos,
                    "layer": layer,
                })
            return result
        except Exception as exc:
            return [{"error": str(exc)}]

    @mcp.tool()
    def get_nets() -> list[dict[str, Any]]:
        """List all nets on the open board."""
        try:
            board = get_kicad().get_board()
            nets = board.get_nets()
            result = []
            for net in nets:
                try:
                    name = str(net.name)
                except Exception:
                    name = ""
                try:
                    code = int(net.net_code)
                except Exception:
                    code = -1
                result.append({"name": name, "code": code})
            return result
        except Exception as exc:
            return [{"error": str(exc)}]

    @mcp.tool()
    def get_tracks() -> list[dict[str, Any]]:
        """List all copper tracks (excluding vias) on the open board."""
        try:
            board = get_kicad().get_board()
            tracks = board.get_tracks()
            result = []
            for t in tracks:
                if _is_via(t):
                    continue
                try:
                    entry = {
                        "start_mm": _pos_to_dict(t.start),
                        "end_mm": _pos_to_dict(t.end),
                        "width_mm": _nm_to_mm(t.width),
                        "layer": str(t.layer),
                        "net": str(t.net.name) if t.net else "",
                    }
                except Exception as field_exc:
                    entry = {"error": str(field_exc)}
                result.append(entry)
            return result
        except Exception as exc:
            return [{"error": str(exc)}]

    @mcp.tool()
    def get_vias() -> list[dict[str, Any]]:
        """List all vias on the open board."""
        try:
            board = get_kicad().get_board()
            tracks = board.get_tracks()
            result = []
            for t in tracks:
                if not _is_via(t):
                    continue
                try:
                    entry = {
                        "position_mm": _pos_to_dict(t.position),
                        "size_mm": _nm_to_mm(t.size),
                        "drill_mm": _nm_to_mm(t.drill),
                        "net": str(t.net.name) if t.net else "",
                    }
                except Exception as field_exc:
                    entry = {"error": str(field_exc)}
                result.append(entry)
            return result
        except Exception as exc:
            return [{"error": str(exc)}]

    @mcp.tool()
    def get_zones() -> list[dict[str, Any]]:
        """List all copper zones on the open board."""
        try:
            board = get_kicad().get_board()
            zones = board.get_zones()
            result = []
            for z in zones:
                try:
                    net_name = str(z.net.name) if z.net else ""
                except Exception:
                    net_name = ""
                try:
                    layer = str(z.layer)
                except Exception:
                    layer = "unknown"
                result.append({"net": net_name, "layer": layer})
            return result
        except Exception as exc:
            return [{"error": str(exc)}]

    @mcp.tool()
    def get_board_outline() -> list[dict[str, Any]]:
        """Return all graphic shapes on the Edge.Cuts layer (board outline)."""
        try:
            board = get_kicad().get_board()
            shapes = board.get_shapes()
            result = []
            for s in shapes:
                try:
                    layer = str(s.layer)
                except Exception:
                    layer = "unknown"
                entry: dict[str, Any] = {"layer": layer, "type": type(s).__name__}
                for attr in ("start", "end", "center", "radius", "width"):
                    try:
                        val = getattr(s, attr)
                        if attr in ("radius", "width"):
                            entry[attr + "_mm"] = _nm_to_mm(val)
                        else:
                            entry[attr + "_mm"] = _pos_to_dict(val)
                    except Exception:
                        pass
                result.append(entry)
            return result
        except Exception as exc:
            return [{"error": str(exc)}]

    @mcp.tool()
    def debug_shapes_layers() -> dict[str, Any]:
        """Return layer values for all shapes on the board, to identify Edge.Cuts layer."""
        try:
            import inspect
            board = get_kicad().get_board()

            # Signature of get_shapes
            try:
                sig = str(inspect.signature(board.get_shapes))
            except Exception as e:
                sig = str(e)

            # All shapes via get_shapes()
            shapes = board.get_shapes()
            seen: dict[str, int] = {}
            for s in shapes:
                try:
                    layer = str(s.layer)
                except Exception:
                    layer = "unknown"
                seen[layer] = seen.get(layer, 0) + 1

            # Try get_items() as well
            items_info: list[str] = []
            try:
                items = board.get_items()
                item_layers: dict[str, int] = {}
                for it in items:
                    try:
                        layer = str(it.layer)
                    except Exception:
                        layer = "unknown"
                    item_layers[layer] = item_layers.get(layer, 0) + 1
                items_info = [f"{k}: {v}" for k, v in sorted(item_layers.items())]
            except Exception as e:
                items_info = [f"get_items error: {e}"]

            return {
                "get_shapes_sig": sig,
                "shapes_by_layer": seen,
                "get_items_by_layer": items_info,
            }
        except Exception as exc:
            return {"error": str(exc)}

    # ------------------------------------------------------------------
    # Write tools
    # ------------------------------------------------------------------

    @mcp.tool()
    def create_track(
        start_x_mm: float,
        start_y_mm: float,
        end_x_mm: float,
        end_y_mm: float,
        width_mm: float,
        layer: str,
        net_name: str = "",
    ) -> str:
        """
        Add a new copper track segment to the board.

        Args:
            start_x_mm: Track start X in millimetres.
            start_y_mm: Track start Y in millimetres.
            end_x_mm:   Track end X in millimetres.
            end_y_mm:   Track end Y in millimetres.
            width_mm:   Track width in millimetres.
            layer:      Layer name, e.g. "F.Cu" or "B.Cu".
            net_name:   Optional net name to assign.
        """
        try:
            from kipy.proto.board.board_types_pb2 import Track
            from kipy.proto.common.types_pb2 import Vector2

            kicad = get_kicad()
            board = kicad.get_board()

            track = Track()
            track.start.CopyFrom(Vector2(x=_mm_to_nm(start_x_mm), y=_mm_to_nm(start_y_mm)))
            track.end.CopyFrom(Vector2(x=_mm_to_nm(end_x_mm), y=_mm_to_nm(end_y_mm)))
            track.width = _mm_to_nm(width_mm)
            track.layer = layer

            if net_name:
                nets = {str(n.name): n for n in board.get_nets()}
                if net_name in nets:
                    track.net.CopyFrom(nets[net_name])

            commit = board.begin_commit()
            board.create_item(track, commit)
            board.push_commit(commit)
            return f"Track created from ({start_x_mm}, {start_y_mm}) to ({end_x_mm}, {end_y_mm}) on {layer}."
        except Exception as exc:
            return f"Failed to create track: {exc}"

    @mcp.tool()
    def move_footprint(reference: str, x_mm: float, y_mm: float) -> str:
        """
        Move a footprint to the given absolute position.

        Args:
            reference: Reference designator, e.g. "R1" or "U3".
            x_mm:      Target X position in millimetres.
            y_mm:      Target Y position in millimetres.
        """
        try:
            kicad = get_kicad()
            board = kicad.get_board()
            footprints = board.get_footprints()

            target = None
            for fp in footprints:
                try:
                    fp_ref = str(fp.reference_field.text.value)
                except Exception:
                    fp_ref = str(fp.reference_field)
                if fp_ref == reference:
                    target = fp
                    break

            if target is None:
                return f"Footprint '{reference}' not found."

            from kipy.geometry import Vector2
            commit = board.begin_commit()
            target.position = Vector2.from_xy(_mm_to_nm(x_mm), _mm_to_nm(y_mm))
            board.update_items([target])
            board.push_commit(commit)
            return f"Moved {reference} to ({x_mm}, {y_mm}) mm."
        except Exception as exc:
            return f"Failed to move footprint '{reference}': {exc}"

    @mcp.tool()
    def batch_move_footprints(moves: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Move multiple footprints in a single undo step.

        Args:
            moves: List of dicts, each with keys:
                   - reference (str): e.g. "R1"
                   - x_mm (float): target X in mm
                   - y_mm (float): target Y in mm
                   - angle (float, optional): rotation in degrees

        Example:
            [{"reference": "R1", "x_mm": 100, "y_mm": 95},
             {"reference": "C1", "x_mm": 102, "y_mm": 95, "angle": 90}]
        """
        try:
            from kipy.geometry import Vector2, Angle
            board = get_kicad().get_board()
            footprints = board.get_footprints()

            # Build reference → footprint map
            fp_map = {}
            for fp in footprints:
                try:
                    ref = str(fp.reference_field.text.value)
                except Exception:
                    ref = str(fp.reference_field)
                fp_map[ref] = fp

            moved, skipped = [], []
            to_update = []

            for move in moves:
                ref = move.get("reference", "")
                fp = fp_map.get(ref)
                if fp is None:
                    skipped.append(ref)
                    continue
                fp.position = Vector2.from_xy(
                    _mm_to_nm(float(move["x_mm"])),
                    _mm_to_nm(float(move["y_mm"])),
                )
                if "angle" in move:
                    fp.orientation = Angle(float(move["angle"]))
                to_update.append(fp)
                moved.append(ref)

            if to_update:
                commit = board.begin_commit()
                board.update_items(to_update)
                board.push_commit(commit)

            return {"moved": moved, "skipped": skipped}
        except Exception as exc:
            return {"error": str(exc)}

    @mcp.tool()
    def rotate_footprint(reference: str, angle: float) -> str:
        """
        Set the rotation angle of a footprint (absolute, in degrees).

        Args:
            reference: Reference designator, e.g. "U1".
            angle:     Rotation angle in degrees (0, 90, 180, 270, etc.).
        """
        try:
            from kipy.geometry import Angle
            board = get_kicad().get_board()
            footprints = board.get_footprints()

            target = None
            for fp in footprints:
                try:
                    fp_ref = str(fp.reference_field.text.value)
                except Exception:
                    fp_ref = str(fp.reference_field)
                if fp_ref == reference:
                    target = fp
                    break

            if target is None:
                return f"Footprint '{reference}' not found."

            commit = board.begin_commit()
            target.orientation = Angle(angle)
            board.update_items([target])
            board.push_commit(commit)
            return f"Rotated {reference} to {angle}°."
        except Exception as exc:
            return f"Failed to rotate '{reference}': {exc}"

    @mcp.tool()
    def get_component_connections(reference: str = "") -> list[dict[str, Any]]:
        """
        Show which components are connected to each other via shared nets.

        If reference is given, returns the connections for that component only.
        If omitted, returns a summary for all components showing which nets
        they're on and which other components share those nets — useful for
        grouping passives near their associated ICs.

        Args:
            reference: Optional reference designator to filter results, e.g. "U1".
        """
        try:
            from kipy.board_types import Pad
            board = get_kicad().get_board()
            footprints = board.get_footprints()

            # Build ref → nets map using footprint definition pads
            ref_nets: dict[str, set[str]] = {}
            for fp in footprints:
                try:
                    ref = str(fp.reference_field.text.value)
                except Exception:
                    ref = str(fp.reference_field)
                nets: set[str] = set()
                try:
                    for item in fp.definition.items:
                        if isinstance(item, Pad):
                            net_name = str(item.net.name)
                            if net_name:
                                nets.add(net_name)
                except Exception:
                    pass
                ref_nets[ref] = nets

            # Build net → refs map
            net_refs: dict[str, list[str]] = {}
            for ref, nets in ref_nets.items():
                for net in nets:
                    net_refs.setdefault(net, []).append(ref)

            # Build result
            result = []
            for fp in footprints:
                try:
                    ref = str(fp.reference_field.text.value)
                except Exception:
                    ref = str(fp.reference_field)

                if reference and ref != reference:
                    continue

                connected: dict[str, list[str]] = {}  # net → [other refs]
                for net in ref_nets.get(ref, set()):
                    others = [r for r in net_refs.get(net, []) if r != ref]
                    if others:
                        connected[net] = sorted(others)

                result.append({
                    "reference": ref,
                    "nets": sorted(ref_nets.get(ref, set())),
                    "connected_to": connected,
                })

            return sorted(result, key=lambda x: x["reference"])
        except Exception as exc:
            return [{"error": str(exc)}]

    @mcp.tool()
    def remove_items_by_id(item_ids: list[str]) -> str:
        """
        Remove board items by their KiCad item ID (KIID).

        Args:
            item_ids: List of item ID strings to remove.
        """
        try:
            kicad = get_kicad()
            board = kicad.get_board()
            commit = board.begin_commit()
            removed = 0
            for item_id in item_ids:
                try:
                    board.remove_item(item_id, commit)
                    removed += 1
                except Exception:
                    pass
            board.push_commit(commit)
            return f"Removed {removed} of {len(item_ids)} item(s)."
        except Exception as exc:
            return f"Failed to remove items: {exc}"

    @mcp.tool()
    def save_board() -> str:
        """Save the current board to disk."""
        try:
            kicad = get_kicad()
            board = kicad.get_board()
            board.save()
            return "Board saved."
        except Exception as exc:
            return f"Failed to save board: {exc}"

    @mcp.tool()
    def refill_zones() -> str:
        """Refill all copper zones on the board."""
        try:
            kicad = get_kicad()
            board = kicad.get_board()
            board.refill_zones()
            return "All zones refilled."
        except Exception as exc:
            return f"Failed to refill zones: {exc}"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_via(track: Any) -> bool:
    """Return True if *track* is a via rather than a plain track segment."""
    try:
        # kipy Via objects have a 'drill' attribute; Track objects do not.
        _ = track.drill
        return True
    except AttributeError:
        return False

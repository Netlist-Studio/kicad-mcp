from kipy import KiCad

_kicad: KiCad | None = None


def get_kicad() -> KiCad:
    global _kicad
    if _kicad is None:
        _kicad = KiCad()
    return _kicad

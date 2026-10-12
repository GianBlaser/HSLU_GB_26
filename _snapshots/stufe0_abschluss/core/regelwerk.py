"""M3 – Regelwerk: Aktion pro IFC-Klasse.

Aktionen: entfernen | verdicken | behalten | fuellen
Stufe 1: Regeln fix im Code. Stufe 2: Regeln aus SQLite, überschreibbar.
"""

AKTIONEN = ("entfernen", "verdicken", "behalten", "fuellen")

# Default-Regelset «Standard 1:200»
DEFAULT_REGELN: dict[str, str] = {
    "IfcWall":                  "behalten",
    "IfcWallStandardCase":      "behalten",
    "IfcSlab":                  "behalten",
    "IfcRoof":                  "behalten",
    "IfcColumn":                "verdicken",
    "IfcBeam":                  "verdicken",
    "IfcStair":                 "behalten",
    "IfcStairFlight":           "behalten",
    "IfcCurtainWall":           "entfernen",
    "IfcPlate":                 "entfernen",
    "IfcMember":                "entfernen",
    "IfcWindow":                "entfernen",
    "IfcDoor":                  "entfernen",
    "IfcRailing":               "entfernen",
    "IfcSpace":                 "entfernen",
    "IfcOpeningElement":        "entfernen",
    "IfcFurnishingElement":     "entfernen",
    "IfcFlowTerminal":          "entfernen",
    "IfcBuildingElementProxy":  "entfernen",
}


class Regelwerk:
    """Verwaltet das aktive Regelset und gibt Aktionen pro Klasse zurück."""

    def __init__(self, regeln: dict[str, str] | None = None):
        self.regeln = regeln or DEFAULT_REGELN.copy()

    def aktion(self, ifc_klasse: str) -> str:
        """Gibt die Aktion für eine IFC-Klasse zurück; unbekannte → behalten."""
        return self.regeln.get(ifc_klasse, "behalten")

    def ist_behalten(self, ifc_klasse: str) -> bool:
        return self.aktion(ifc_klasse) in ("behalten", "verdicken", "fuellen")

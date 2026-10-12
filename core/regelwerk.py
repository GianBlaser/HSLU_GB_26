"""M2 – Regelwerk: Aktion und Kategorie pro IFC-Klasse.

Aktionen: entfernen | verdicken | behalten | fuellen
Stufe 1: Regeln fix im Code. Stufe 2: Regeln aus SQLite, überschreibbar.
"""

import pandas as pd

AKTIONEN = ("entfernen", "verdicken", "behalten", "fuellen")

# Lesbare Kategorie pro IFC-Klasse (für die Bauteiltabelle in der UI)
KATEGORIEN: dict[str, str] = {
    "IfcWall":                  "Wand",
    "IfcWallStandardCase":      "Wand",
    "IfcSlab":                  "Decke",
    "IfcRoof":                  "Dach",
    "IfcColumn":                "Stütze",
    "IfcBeam":                  "Träger",
    "IfcStair":                 "Treppe",
    "IfcStairFlight":           "Treppe",
    "IfcCurtainWall":           "Verglasung",
    "IfcPlate":                 "Verglasung",
    "IfcMember":                "Verglasung",
    "IfcWindow":                "Öffnung",
    "IfcDoor":                  "Öffnung",
    "IfcRailing":               "Geländer",
    "IfcSpace":                 "Raum",
    "IfcOpeningElement":        "Öffnung",
    "IfcFurnishingElement":     "Möblierung",
    "IfcFlowTerminal":          "Haustechnik",
    "IfcBuildingElementProxy":  "Sonstiges",
}
KATEGORIE_UNBEKANNT = "Sonstiges"

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

    def kategorie(self, ifc_klasse: str) -> str:
        """Gibt die lesbare Kategorie für eine IFC-Klasse zurück."""
        return KATEGORIEN.get(ifc_klasse, KATEGORIE_UNBEKANNT)

    def klassifizieren(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ergänzt den Bauteil-DataFrame um aktion, drucken und kategorie.

        Erwartet eine Spalte 'klasse' (IFC-Klasse). Gibt eine Kopie zurück,
        der Eingabe-DataFrame bleibt unverändert.
        """
        df = df.copy()
        df["aktion"] = df["klasse"].map(self.aktion)
        df["drucken"] = df["klasse"].map(self.ist_behalten)
        df["kategorie"] = df["klasse"].map(self.kategorie)
        return df

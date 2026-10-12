"""M2 – Massstabsumrechnung und Druckbarkeitsprüfung.

Berechnet pro Bauteil den Status: druckbar / kritisch / nicht druckbar.
"""

import pandas as pd
from config import MINDESTWAND_MM, KRITISCH_BIS_MM, BAURAUM_X_MM, BAURAUM_Y_MM, BAURAUM_Z_MM


STATUS_DRUCKBAR = "druckbar"
STATUS_KRITISCH = "kritisch"
STATUS_NICHT_DRUCKBAR = "nicht_druckbar"


def modellmass(reales_mass_mm: float, massstab: int) -> float:
    """Skaliert ein reales Mass (mm) auf den Modellmassstab."""
    return reales_mass_mm / massstab


def druckbarkeits_status(dicke_modell_mm: float) -> str:
    """Gibt den Druckbarkeitsstatus für eine Modelldicke zurück."""
    if dicke_modell_mm >= KRITISCH_BIS_MM:
        return STATUS_DRUCKBAR
    if dicke_modell_mm >= MINDESTWAND_MM:
        return STATUS_KRITISCH
    return STATUS_NICHT_DRUCKBAR


def status_spalte_hinzufuegen(df: pd.DataFrame, massstab: int) -> pd.DataFrame:
    """Ergänzt den DataFrame um die Spalte 'status' (Stufe 1)."""
    raise NotImplementedError("Stufe 1")


def bauraum_pruefen(bbox_xyz_mm: tuple[float, float, float]) -> bool:
    """Gibt True zurück, wenn das Objekt in den Bauraum passt."""
    x, y, z = bbox_xyz_mm
    return x <= BAURAUM_X_MM and y <= BAURAUM_Y_MM and z <= BAURAUM_Z_MM

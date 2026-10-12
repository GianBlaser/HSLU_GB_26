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
    """Ergänzt den Bauteil-DataFrame um Modellmass, Status und Bauraum-Check.

    Erwartet die realen BBox-Spalten bbox_x_mm / bbox_y_mm / bbox_z_mm und
    dicke_min_mm (Massstab 1:1), wie von IfcModell.bauteile_laden() geliefert.
    Neue Spalten:
      - dicke_modell_mm:   kleinste Kante im Modellmassstab
      - status:            druckbar | kritisch | nicht_druckbar (NaN-Dicke → nicht_druckbar)
      - bbox_volumen_mm3:  reales BBox-Volumen (1:1)
      - passt_in_bauraum:  bool, ob das Bauteil skaliert in den Bauraum passt
    Gibt eine Kopie zurück, der Eingabe-DataFrame bleibt unverändert.
    """
    df = df.copy()
    df["dicke_modell_mm"] = df["dicke_min_mm"] / massstab
    df["status"] = df["dicke_modell_mm"].map(
        lambda d: STATUS_NICHT_DRUCKBAR if pd.isna(d) else druckbarkeits_status(d)
    )
    df["bbox_volumen_mm3"] = df["bbox_x_mm"] * df["bbox_y_mm"] * df["bbox_z_mm"]
    df["passt_in_bauraum"] = df.apply(
        lambda r: _passt_in_bauraum(r, massstab), axis=1
    )
    return df


def _passt_in_bauraum(zeile: pd.Series, massstab: int) -> bool:
    """True, wenn die skalierte BBox einer Zeile in den Bauraum passt (NaN → False)."""
    dims = zeile[["bbox_x_mm", "bbox_y_mm", "bbox_z_mm"]]
    if dims.isna().any():
        return False
    return bauraum_pruefen(tuple(d / massstab for d in dims))


def bauraum_pruefen(bbox_xyz_mm: tuple[float, float, float]) -> bool:
    """Gibt True zurück, wenn das Objekt in den Bauraum passt."""
    x, y, z = bbox_xyz_mm
    return x <= BAURAUM_X_MM and y <= BAURAUM_Y_MM and z <= BAURAUM_Z_MM

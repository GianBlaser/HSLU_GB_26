"""Einfache Tests für Druckbarkeits-Logik."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

from core.druckbarkeit import (
    druckbarkeits_status, modellmass, bauraum_pruefen, status_spalte_hinzufuegen,
)


def test_status_druckbar():
    assert druckbarkeits_status(1.5) == "druckbar"


def test_status_kritisch():
    assert druckbarkeits_status(1.0) == "kritisch"


def test_status_nicht_druckbar():
    assert druckbarkeits_status(0.3) == "nicht_druckbar"


def test_modellmass_1_200():
    assert abs(modellmass(20000, 200) - 100.0) < 1e-9


def test_bauraum_passt():
    assert bauraum_pruefen((100.0, 80.0, 120.0)) is True


def test_bauraum_passt_nicht():
    assert bauraum_pruefen((300.0, 210.0, 220.0)) is False


def _bauteil_df():
    """Drei Bauteile in realen mm plus eins ohne Geometrie (NaN)."""
    return pd.DataFrame({
        "klasse":       ["IfcWall", "IfcSlab", "IfcColumn", "IfcSpace"],
        "bbox_x_mm":    [5000.0, 8000.0, 300.0, np.nan],
        "bbox_y_mm":    [240.0, 6000.0, 300.0, np.nan],
        "bbox_z_mm":    [3000.0, 200.0, 3000.0, np.nan],
        "dicke_min_mm": [240.0, 200.0, 300.0, np.nan],
    })


def test_status_spalte_massstab_200():
    df = status_spalte_hinzufuegen(_bauteil_df(), massstab=200)
    # 240/200 = 1.2 mm → druckbar; 200/200 = 1.0 → kritisch; 300/200 = 1.5 → druckbar
    assert list(df["status"]) == ["druckbar", "kritisch", "druckbar", "nicht_druckbar"]


def test_status_spalte_volumen_und_bauraum():
    df = status_spalte_hinzufuegen(_bauteil_df(), massstab=200)
    assert abs(df.loc[1, "bbox_volumen_mm3"] - 8000.0 * 6000.0 * 200.0) < 1e-3
    # Wand 1:200 = 25 x 1.2 x 15 mm passt; NaN-Zeile passt nicht
    assert df.loc[0, "passt_in_bauraum"] == True
    assert df.loc[3, "passt_in_bauraum"] == False

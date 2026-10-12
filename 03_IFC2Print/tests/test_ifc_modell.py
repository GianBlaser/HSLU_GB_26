"""Tests für M1 – IFC-Import und Bauteilanalyse."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pytest

from core.ifc_modell import IfcModell

TESTDATEI = Path(__file__).parent.parent / "testdaten" / "Building-Architecture-IFC2x3.ifc"

ERWARTETE_SPALTEN = {
    "guid", "klasse", "name", "geschoss",
    "bbox_x_mm", "bbox_y_mm", "bbox_z_mm", "dicke_min_mm",
}


@pytest.fixture(scope="module")
def modell():
    return IfcModell(str(TESTDATEI))


def test_oeffnen_setzt_schema(modell):
    assert modell.schema.startswith("IFC")


def test_bauteile_ohne_geometrie_schnell(modell):
    """mit_geometrie=False liefert Stammdaten, BBox-Spalten sind NaN."""
    df = modell.bauteile_laden(mit_geometrie=False)
    assert not df.empty
    assert ERWARTETE_SPALTEN.issubset(df.columns)
    assert df["bbox_x_mm"].isna().all()
    # Jede Zeile hat eine GUID und eine IFC-Klasse
    assert df["guid"].notna().all()
    assert df["klasse"].str.startswith("Ifc").all()


def test_bauteile_mit_geometrie_haben_bbox(modell):
    """Mit Geometrie sind BBox-Masse positiv und dicke_min = kleinste Kante."""
    df = modell.bauteile_laden(mit_geometrie=True)
    assert not df.empty
    mit_bbox = df.dropna(subset=["bbox_x_mm", "bbox_y_mm", "bbox_z_mm"])
    assert len(mit_bbox) > 0, "Mindestens ein Bauteil sollte Geometrie haben"
    assert (mit_bbox[["bbox_x_mm", "bbox_y_mm", "bbox_z_mm"]] > 0).all().all()
    erwartet_min = mit_bbox[["bbox_x_mm", "bbox_y_mm", "bbox_z_mm"]].min(axis=1)
    assert np.allclose(mit_bbox["dicke_min_mm"], erwartet_min)


def test_geschosse_hoehen_sortiert(modell):
    hoehen = modell.geschosse_hoehen(massstab=200)
    z_werte = [z for _, z in hoehen]
    assert z_werte == sorted(z_werte)

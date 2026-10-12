"""Tests für das Regelwerk."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from core.regelwerk import Regelwerk


def test_bekannte_klasse_entfernen():
    rw = Regelwerk()
    assert rw.aktion("IfcDoor") == "entfernen"


def test_bekannte_klasse_behalten():
    rw = Regelwerk()
    assert rw.aktion("IfcWall") == "behalten"


def test_unbekannte_klasse_behalten():
    rw = Regelwerk()
    assert rw.aktion("IfcUnbekanntesElement") == "behalten"


def test_ist_behalten():
    rw = Regelwerk()
    assert rw.ist_behalten("IfcWall") is True
    assert rw.ist_behalten("IfcRailing") is False


def test_kategorie():
    rw = Regelwerk()
    assert rw.kategorie("IfcSlab") == "Decke"
    assert rw.kategorie("IfcUnbekannt") == "Sonstiges"


def test_klassifizieren_fuegt_spalten_an():
    rw = Regelwerk()
    df = pd.DataFrame({"klasse": ["IfcWall", "IfcDoor", "IfcColumn"]})
    out = rw.klassifizieren(df)
    assert list(out["drucken"]) == [True, False, True]
    assert list(out["kategorie"]) == ["Wand", "Öffnung", "Stütze"]
    assert list(out["aktion"]) == ["behalten", "entfernen", "verdicken"]
    # Eingabe bleibt unverändert
    assert "drucken" not in df.columns

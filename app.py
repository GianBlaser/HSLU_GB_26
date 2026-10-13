"""IFC2Print – Hauptkomponente (Streamlit-UI).

Ablauf: Upload → Analyse (M1 Bauteile, M2 Regelwerk, M3 Druckbarkeit) →
STL erzeugen (Stufe-0-Pipeline) → Download.

Start:  streamlit run app.py
"""

import hashlib
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from config import VOXEL_PITCH_MM
from core.ifc_modell import IfcModell
from core.regelwerk import Regelwerk
from core.druckbarkeit import status_spalte_hinzufuegen
from core.huelle import huelle_erzeugen

MASSSTAEBE = {"1:50": 50, "1:100": 100, "1:200": 200}

st.set_page_config(page_title="IFC2Print", layout="wide")
st.title("IFC2Print – Massstabsmodell-Generator")


@st.cache_resource(show_spinner="IFC-Datei wird geöffnet …")
def lade_ifc(file_bytes: bytes, file_hash: str) -> IfcModell:
    """Schreibt den Upload in eine Temp-Datei und öffnet ihn als IfcModell.

    file_hash geht nur in den Cache-Schlüssel ein (identische Datei → Cache-Treffer).
    """
    tmp = Path(tempfile.gettempdir()) / f"ifc2print_{file_hash}.ifc"
    tmp.write_bytes(file_bytes)
    return IfcModell(str(tmp))


@st.cache_data(show_spinner="Bauteile werden analysiert (Triangulierung) …")
def analysiere(_ifc: IfcModell, file_hash: str) -> pd.DataFrame:
    """Lädt die Bauteile inkl. Geometrie. Cache-Schlüssel: file_hash."""
    return _ifc.bauteile_laden(mit_geometrie=True)


@st.cache_data(show_spinner="Modell wird erzeugt (Voxel-Hülle) …")
def erzeuge_stl(_ifc: IfcModell, file_hash: str, massstab: int,
                klassen: tuple[str, ...]) -> tuple[bytes, bool]:
    """Erzeugt die wasserdichte Voxel-Hülle und gibt (STL-Bytes, wasserdicht) zurück."""
    _, meshes, _ = _ifc.rohnetz_erzeugen(set(klassen), massstab)
    # Threads statt Prozesse: ProcessPool scheitert unter Streamlit/Windows am spawn-Reimport.
    huelle, _, _, _ = huelle_erzeugen(meshes, VOXEL_PITCH_MM, parallel="thread")
    return huelle.export(file_type="stl"), bool(huelle.is_watertight)


upload = st.file_uploader("IFC-Datei hochladen", type=["ifc"])
massstab_label = st.radio("Massstab", list(MASSSTAEBE), index=2, horizontal=True)
massstab = MASSSTAEBE[massstab_label]

if upload is None:
    st.info("Lade eine IFC-Datei hoch, um die Bauteilanalyse zu starten.")
    st.stop()

file_bytes = upload.getvalue()
file_hash = hashlib.sha1(file_bytes).hexdigest()[:16]

ifc = lade_ifc(file_bytes, file_hash)
df = analysiere(ifc, file_hash)

# M2 Regelwerk + M3 Druckbarkeit anwenden (günstig, bei jedem Rerun)
regelwerk = Regelwerk()
df = regelwerk.klassifizieren(df)
df = status_spalte_hinzufuegen(df, massstab)

# --- Kennzahlen ---
k1, k2, k3, k4 = st.columns(4)
k1.metric("Schema", ifc.schema)
k2.metric("Bauteile", len(df))
k3.metric("Gedruckt", int(df["drucken"].sum()))
k4.metric("Nicht druckbar", int((df["status"] == "nicht_druckbar").sum()))

# --- Bauteiltabelle ---
st.subheader("Bauteile")
nur_drucken = st.checkbox("Nur zu druckende Bauteile anzeigen", value=False)
anzeige = df[df["drucken"]] if nur_drucken else df
spalten = ["kategorie", "klasse", "name", "geschoss",
           "dicke_modell_mm", "status", "drucken"]
st.dataframe(
    anzeige[spalten].rename(columns={
        "kategorie": "Kategorie", "klasse": "IFC-Klasse", "name": "Name",
        "geschoss": "Geschoss", "dicke_modell_mm": "Dicke Modell (mm)",
        "status": "Status", "drucken": "Drucken",
    }).style.format({"Dicke Modell (mm)": "{:.2f}"}),
    width="stretch", hide_index=True,
)

# --- STL erzeugen ---
st.subheader("3D-Modell")
behalten_klassen = tuple(sorted(df.loc[df["drucken"], "klasse"].unique()))
st.caption("Gedruckte IFC-Klassen: " + (", ".join(behalten_klassen) or "–"))

if not behalten_klassen:
    st.warning("Keine druckbaren Bauteile – nichts zu erzeugen.")
elif st.button("STL erzeugen", type="primary"):
    stl_bytes, wasserdicht = erzeuge_stl(ifc, file_hash, massstab, behalten_klassen)
    if wasserdicht:
        st.success("Wasserdichtes Modell erzeugt.")
    else:
        st.warning("Modell erzeugt, aber nicht wasserdicht – im Slicer prüfen.")
    st.download_button(
        "STL herunterladen",
        data=stl_bytes,
        file_name=f"{Path(upload.name).stem}_1_{massstab:03d}.stl",
        mime="model/stl",
    )

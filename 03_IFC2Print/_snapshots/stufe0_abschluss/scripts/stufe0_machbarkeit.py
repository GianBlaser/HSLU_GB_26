"""Stufe 0 – Machbarkeitstest: IFC → Rohnetz → Voxel-Hülle → STL.

Ausführen (aus dem Ordner 03_IFC2Print, venv aktiv):
    python scripts/stufe0_machbarkeit.py

Die eigentliche Logik liegt in core/ifc_modell.py und core/huelle.py.
Dieses Skript ruft sie nur auf und misst Laufzeiten für die README.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # Projektordner importierbar

from config import MASSSTAB_DEFAULT, VOXEL_PITCH_MM
from core.ifc_modell import IfcModell
from core.huelle import huelle_erzeugen

# Originaldatei: ARC_Modell_NEST_230328.ifc (sobald verfügbar ersetzen)
IFC_PFAD = Path("testdaten/TEST-File_1.ifc")
OUTPUT_DIR = Path("output")

# Klassen für die Hülle in Stufe 0 (ab Stufe 1 über core/regelwerk.py)
KLASSEN_BEHALTEN = {"IfcWall", "IfcWallStandardCase", "IfcSlab", "IfcRoof", "IfcColumn", "IfcBeam"}


def main():
    if not IFC_PFAD.exists():
        sys.exit(f"FEHLER: IFC-Datei nicht gefunden: {IFC_PFAD}")
    OUTPUT_DIR.mkdir(exist_ok=True)
    t_start = time.perf_counter()

    print("--- Schritt 1: IFC einlesen ---")
    ifc = IfcModell(IFC_PFAD)
    df = ifc.bauteile_laden()
    print(f"Schema: {ifc.schema}, Bauteile: {len(df)}")
    print(df["klasse"].value_counts().head(15).to_string())
    print(df["geschoss"].value_counts().to_string())

    print("\n--- Schritt 2: Triangulieren ---")
    t0 = time.perf_counter()
    rohnetz, meshes, n_fehler = ifc.rohnetz_erzeugen(KLASSEN_BEHALTEN, MASSSTAB_DEFAULT)
    rohnetz.export(str(OUTPUT_DIR / "rohnetz.stl"))
    print(f"Meshes: {len(meshes)}, ohne Geometrie: {n_fehler}, Faces: {len(rohnetz.faces)}")
    print(f"BBox (mm): {rohnetz.bounding_box.extents.round(1)}")
    print(f"Laufzeit Triangulierung: {time.perf_counter() - t0:.1f} s")

    print("\n--- Schritt 3: Voxel-Hülle ---")
    t0 = time.perf_counter()
    huelle, info = huelle_erzeugen(meshes, VOXEL_PITCH_MM)
    huelle.export(str(OUTPUT_DIR / f"huelle_1_{MASSSTAB_DEFAULT}.stl"))
    print(f"Voxelmatrix: {info['voxelmatrix']}, gefüllt: {info['gefuellte_voxel']:,}, RAM: {info['ram_mb']:.1f} MB, Bauteile nicht dicht (übersprungen): {info['nicht_dicht']}")
    print(f"Faces: {len(huelle.faces):,}, Wasserdicht: {huelle.is_watertight}")
    print(f"Laufzeit Voxel-Hülle: {time.perf_counter() - t0:.1f} s")

    print(f"\n=== Gesamtlaufzeit: {time.perf_counter() - t_start:.1f} s ===")


if __name__ == "__main__":
    main()

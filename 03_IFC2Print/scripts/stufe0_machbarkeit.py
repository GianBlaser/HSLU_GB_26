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
from core.huelle import huelle_erzeugen, matrix_zu_mesh

# Originaldatei: ARC_Modell_NEST_230328.ifc (sobald verfügbar ersetzen)
IFC_PFAD = Path("testdaten/MFH_eBKPH_Test.ifc")
OUTPUT_DIR = Path("output")
PHASE = 0

# Klassen für die Hülle in Stufe 0 (ab Stufe 1 über core/regelwerk.py)
KLASSEN_BEHALTEN = {"IfcWall", "IfcWallStandardCase", "IfcSlab", "IfcRoof", "IfcColumn", "IfcBeam"}


def naechste_version(muster: str) -> str:
    """Gibt den nächsten freien Dateinamen zurück (V01, V02, …)."""
    v = 1
    while True:
        name = muster.format(v=f"{v:02d}")
        if not (OUTPUT_DIR / name).exists():
            return name
        v += 1


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
    rohnetz.export(str(OUTPUT_DIR / naechste_version(f"Rohnetz_P{PHASE}_V{{v}}.stl")))
    print(f"Meshes: {len(meshes)}, ohne Geometrie: {n_fehler}, Faces: {len(rohnetz.faces)}")
    print(f"BBox (mm): {rohnetz.bounding_box.extents.round(1)}")
    print(f"Laufzeit Triangulierung: {time.perf_counter() - t0:.1f} s")

    print("\n--- Schritt 3: Voxel-Hülle ---")
    t0 = time.perf_counter()
    huelle, matrix, vox_transform, info = huelle_erzeugen(meshes, VOXEL_PITCH_MM)
    huelle.export(str(OUTPUT_DIR / naechste_version(f"Box_1_{MASSSTAB_DEFAULT:03d}_P{PHASE}_V{{v}}.stl")))
    print(f"Voxelmatrix: {info['voxelmatrix']}, gefüllt: {info['gefuellte_voxel']:,}, RAM: {info['ram_mb']:.1f} MB, Bauteile nicht dicht (übersprungen): {info['nicht_dicht']}")
    print(f"Faces: {len(huelle.faces):,}, Wasserdicht: {huelle.is_watertight}")
    print(f"Laufzeit Voxel-Hülle: {time.perf_counter() - t0:.1f} s")

    print("\n--- Schritt 4: Stockwerke ---")
    t0 = time.perf_counter()
    geschosse = ifc.geschosse_hoehen(MASSSTAB_DEFAULT)
    print(f"Geschosse: {[(n, round(z, 1)) for n, z in geschosse]}")
    pitch = VOXEL_PITCH_MM
    z0 = vox_transform[2, 3]  # Z-Koordinate des ersten Voxel-Zentrums
    z_max = z0 + matrix.shape[2] * pitch
    for i, (name, z_mm) in enumerate(geschosse):
        z_oben = geschosse[i + 1][1] if i + 1 < len(geschosse) else z_max
        iz0 = max(0, round((z_mm - z0) / pitch))
        iz1 = min(matrix.shape[2], round((z_oben - z0) / pitch))
        if iz1 <= iz0:
            continue
        slice_mat = matrix[:, :, iz0:iz1]
        if not slice_mat.any():
            continue
        # Deckenplatte abschneiden: alle aufeinanderfolgenden dichten Lagen von oben
        # vollständig entfernen (Platte ist mehrere Voxel-Schichten dick).
        threshold = 0.3
        iz = slice_mat.shape[2] - 1
        while iz >= 0 and slice_mat[:, :, iz].mean() > threshold:
            iz -= 1
        slice_mat = slice_mat[:, :, :iz + 1]
        if not slice_mat.any():
            continue
        t = vox_transform.copy()
        t[2, 3] = z0 + iz0 * pitch
        mesh = matrix_zu_mesh(slice_mat, t)
        sname = name.replace(" ", "_").replace(".", "")
        fname = naechste_version(f"Etage_{sname}_P{PHASE}_V{{v}}.stl")
        mesh.export(str(OUTPUT_DIR / fname))
        print(f"  {name}: {slice_mat.sum():,} Voxel, {len(mesh.faces):,} Faces -> {fname}")
    print(f"Laufzeit Stockwerke: {time.perf_counter() - t0:.1f} s")

    print(f"\n=== Gesamtlaufzeit: {time.perf_counter() - t_start:.1f} s ===")


if __name__ == "__main__":
    main()

"""M4 – Hüllengenerierung: Surface-Voxelisierung → binary_closing/fill_holes → Marching Cubes.

Voxelisierung via method='ray' (RAM-effizient, kein edge-subdivision).
binary_closing schliesst Öffnungen (Fenster, Türen) in der Voxelschale.
binary_fill_holes füllt das Innere.
VoxelGrid.marching_cubes erzeugt wasserdichtes Mesh (Koordinaten korrekt).
"""

import numpy as np
import trimesh
from scipy.ndimage import binary_closing, binary_fill_holes
from trimesh.voxel import VoxelGrid


def huelle_erzeugen(meshes: list[trimesh.Trimesh], pitch_mm: float) -> tuple[trimesh.Trimesh, dict]:
    """Erzeugt aus den Einzelnetzen der Bauteile eine wasserdichte Voxel-Hülle.

    Rückgabe: (Hülle, Info-Dict mit voxelmatrix, gefuellte_voxel, ram_mb, nicht_dicht).
    """
    alle = trimesh.util.concatenate(meshes)
    nicht_dicht = sum(1 for m in meshes if not m.is_watertight)

    # Surface-Voxelisierung: method='ray' vermeidet MemoryError beim edge-subdivision
    voxgrid = alle.voxelized(pitch=pitch_mm, method='ray')

    # closing(5): schliesst Öffnungen bis 5 Voxel = 2 mm bei 0.4mm pitch (Fenster/Türen 1:200)
    matrix = binary_closing(voxgrid.matrix, iterations=5)
    matrix = binary_fill_holes(matrix)

    info = {
        "voxelmatrix":     matrix.shape,
        "gefuellte_voxel": int(matrix.sum()),
        "ram_mb":          matrix.nbytes / 1e6,
        "nicht_dicht":     nicht_dicht,
    }

    # VoxelGrid.marching_cubes verwendet die richtige Koordinatentransformation
    # und produziert ein korrekt indiziertes wasserdichtes Mesh
    grid = VoxelGrid(matrix, transform=voxgrid.transform)
    huelle = grid.marching_cubes
    huelle.fix_normals()
    return huelle, info


def ist_wasserdicht(mesh: trimesh.Trimesh) -> bool:
    return mesh.is_watertight

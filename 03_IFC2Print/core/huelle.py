"""M4 – Hüllengenerierung: Per-Element-Voxelisierung (parallel) → Marching Cubes.

Jedes Element wird mit method='subdivide' voxelisiert und anschliessend per
binary_fill_holes EINZELN aufgefüllt: Wandhohlräume (Schalen) werden solid, Räume
bleiben hohl (kein einzelnes Element umschliesst einen ganzen Raum). Kein
binary_closing auf der Globalmatrix (füllt sonst ganze Ebenen/Räume auf).
Parallelisierung via ProcessPoolExecutor über alle CPU-Kerne.
"""

import multiprocessing
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import trimesh
from scipy.ndimage import binary_fill_holes
from trimesh.voxel import VoxelGrid


def _voxelize_mesh(args: tuple) -> tuple[np.ndarray, np.ndarray]:
    """Worker: voxelisiert ein einzelnes Mesh und füllt sein Inneres (läuft im Worker-Prozess).

    binary_fill_holes pro Element füllt den Hohlraum innerhalb des Elements (z.B. den
    Luftspalt zwischen Wandschalen). Räume bleiben hohl, weil kein einzelnes Element
    den ganzen Raum umschliesst — der Raumhohlraum erstreckt sich über mehrere Elemente.
    """
    verts, faces, pitch_mm = args
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    try:
        vox = mesh.voxelized(pitch=pitch_mm, method='subdivide')
    except Exception:
        vox = mesh.voxelized(pitch=pitch_mm, method='ray')
    filled = binary_fill_holes(vox.matrix)
    return np.array(vox.transform[:3, 3]), filled


def huelle_erzeugen(meshes: list[trimesh.Trimesh], pitch_mm: float) -> tuple[trimesh.Trimesh, dict]:
    """Erzeugt aus den Einzelnetzen der Bauteile eine wasserdichte Voxel-Hülle.

    Rückgabe: (Hülle, Info-Dict mit voxelmatrix, gefuellte_voxel, ram_mb, nicht_dicht).
    """
    alle = trimesh.util.concatenate(meshes)
    nicht_dicht = sum(1 for m in meshes if not m.is_watertight)

    unten = alle.bounds[0] - pitch_mm
    shape = tuple(
        int(np.ceil((alle.bounds[1][i] - alle.bounds[0][i]) / pitch_mm)) + 3
        for i in range(3)
    )
    matrix = np.zeros(shape, dtype=bool)

    args = [(m.vertices, m.faces, pitch_mm) for m in meshes]
    workers = max(1, multiprocessing.cpu_count() - 1)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for vox_origin, vox_matrix in ex.map(_voxelize_mesh, args):
            offset = np.round((vox_origin - (unten + pitch_mm / 2)) / pitch_mm).astype(int)
            idx = np.array(np.where(vox_matrix)).T
            global_idx = idx + offset
            valid = np.all((global_idx >= 0) & (global_idx < shape), axis=1)
            g = global_idx[valid]
            if len(g):
                matrix[g[:, 0], g[:, 1], g[:, 2]] = True

    # KEIN binary_closing: Das 3D-Closing überbrückt eng benachbarte horizontale
    # Flächen (Platten-Ober-/Unterseiten, Simse) und erzeugte dadurch komplett
    # massive Ebenen quer über die Grundfläche – das füllte die Innenräume auf.
    # Echte Böden/Decken sind durch die Voxelisierung bereits solide.

    transform = np.eye(4)
    transform[:3, 3] = unten + pitch_mm / 2
    transform[0, 0] = transform[1, 1] = transform[2, 2] = pitch_mm

    info = {
        "voxelmatrix":     matrix.shape,
        "gefuellte_voxel": int(matrix.sum()),
        "ram_mb":          matrix.nbytes / 1e6,
        "nicht_dicht":     nicht_dicht,
    }

    return matrix_zu_mesh(matrix, transform), matrix, transform, info


def matrix_zu_mesh(matrix: np.ndarray, transform: np.ndarray) -> trimesh.Trimesh:
    """Konvertiert eine Bool-Voxelmatrix via Marching Cubes in ein Trimesh.

    Achtung: VoxelGrid.marching_cubes (trimesh 5.1.1) liefert das Mesh in
    reinen Voxel-Index-Koordinaten und ignoriert den übergebenen Transform
    (weder Pitch-Skalierung noch Verschiebung). Daher den Transform hier
    explizit anwenden – sonst sind alle STL ~1/pitch-fach zu gross.
    """
    grid = VoxelGrid(matrix, transform=transform)
    mesh = grid.marching_cubes
    mesh.apply_transform(transform)
    mesh.fix_normals()
    return mesh


def ist_wasserdicht(mesh: trimesh.Trimesh) -> bool:
    return mesh.is_watertight

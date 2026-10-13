"""M4 – Hüllengenerierung: Per-Element-Voxelisierung (parallel) → Marching Cubes.

Jedes Element wird mit method='subdivide' voxelisiert und anschliessend per
binary_fill_holes EINZELN aufgefüllt: Wandhohlräume (Schalen) werden solid, Räume
bleiben hohl (kein einzelnes Element umschliesst einen ganzen Raum). Kein
binary_closing auf der Globalmatrix (füllt sonst ganze Ebenen/Räume auf).
Parallelisierung wählbar: Prozesse (CLI), Threads (Streamlit-sicher) oder
sequenziell. Prozesse scheitern unter Streamlit/Windows am spawn-Reimport
(BrokenProcessPool) → automatischer Fallback auf sequenziell.
"""

import multiprocessing
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from concurrent.futures.process import BrokenProcessPool

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


def _voxelisiere_alle(args: list[tuple], parallel: str) -> list[tuple[np.ndarray, np.ndarray]]:
    """Voxelisiert alle Elemente im gewählten Modus und gibt die Ergebnisse als Liste zurück.

    parallel: 'process' (CLI, schnell) | 'thread' (Streamlit-sicher) | 'none' (sequenziell).
    Bei 'process' wird auf BrokenProcessPool (z.B. unter Streamlit) sequenziell wiederholt.
    """
    workers = max(1, multiprocessing.cpu_count() - 1)
    if parallel == "process":
        try:
            with ProcessPoolExecutor(max_workers=workers) as ex:
                return list(ex.map(_voxelize_mesh, args))
        except BrokenProcessPool:
            pass  # Fallback: sequenziell (siehe unten)
    elif parallel == "thread":
        with ThreadPoolExecutor(max_workers=workers) as ex:
            return list(ex.map(_voxelize_mesh, args))
    return [_voxelize_mesh(a) for a in args]


def huelle_erzeugen(meshes: list[trimesh.Trimesh], pitch_mm: float,
                    parallel: str = "process") -> tuple[trimesh.Trimesh, dict]:
    """Erzeugt aus den Einzelnetzen der Bauteile eine wasserdichte Voxel-Hülle.

    parallel: 'process' (CLI), 'thread' (Streamlit-sicher) oder 'none'.
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
    for vox_origin, vox_matrix in _voxelisiere_alle(args, parallel):
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

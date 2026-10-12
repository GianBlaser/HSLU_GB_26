"""M6 – Export: STL und 3MF."""

import trimesh
from pathlib import Path


def als_stl_speichern(mesh: trimesh.Trimesh, pfad: Path) -> None:
    """Speichert ein Trimesh-Objekt als STL-Datei."""
    mesh.export(str(pfad))


def als_3mf_speichern(meshes: list[trimesh.Trimesh], pfad: Path) -> None:
    """Speichert mehrere Teile als 3MF (Stufe 3)."""
    raise NotImplementedError("Stufe 3")

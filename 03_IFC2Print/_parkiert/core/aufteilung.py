"""M5 – Geschossweise Aufteilung und Steckverbinder (Stufe 3).

Schneidet das Modell auf Oberkante Rohdecke je Geschoss und platziert
Steckzapfen automatisch auf den Schnittflächen.
"""

import trimesh


def geschosse_schneiden(mesh: trimesh.Trimesh, schnitthoehen_mm: list[float]) -> list[trimesh.Trimesh]:
    """Schneidet das Netz an den angegebenen Z-Höhen und gibt Teile zurück."""
    raise NotImplementedError("Stufe 3")


def zapfen_platzieren(teil_oben: trimesh.Trimesh, teil_unten: trimesh.Trimesh) -> tuple[trimesh.Trimesh, trimesh.Trimesh]:
    """Fügt Zapfen (oben) und Löcher (unten) an der Fuge ein."""
    raise NotImplementedError("Stufe 3")

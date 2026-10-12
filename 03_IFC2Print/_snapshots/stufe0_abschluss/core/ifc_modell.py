"""M1 – IFC-Import und Bauteilanalyse.

Klasse IfcModell: lädt eine IFC-Datei, liefert eine Pandas-Tabelle aller
Bauteile (GUID, Klasse, Name, Geschoss) und trianguliert ausgewählte
Klassen zu einem Rohnetz.
Stufe 1 ergänzt: BBox und minimale Dicke pro Bauteil.
"""

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import numpy as np
import pandas as pd
import trimesh


class IfcModell:
    """Kapselt eine geöffnete IFC-Datei und die Bauteilanalyse."""

    def __init__(self, pfad: str):
        """Öffnet die IFC-Datei und löst einen Fehler aus, falls ungültig."""
        self.pfad = pfad
        self.modell = ifcopenshell.open(str(pfad))
        self.schema = self.modell.schema
        self.bauteile_df: pd.DataFrame | None = None

    def bauteile_laden(self) -> pd.DataFrame:
        """Gibt DataFrame aller IfcProduct-Instanzen mit Darstellung zurück."""
        zeilen = []
        for element in self.modell.by_type("IfcProduct"):
            if not element.Representation:
                continue
            zeilen.append({
                "guid":     element.GlobalId,
                "klasse":   element.is_a(),
                "name":     getattr(element, "Name", ""),
                "geschoss": self.geschoss_fuer(element),
            })
        self.bauteile_df = pd.DataFrame(zeilen)
        return self.bauteile_df

    def geschoss_fuer(self, element) -> str:
        """Gibt den Namen des Geschosses für ein Element zurück."""
        container = ifcopenshell.util.element.get_container(element)
        if container is None:
            return "unbekannt"
        return container.Name or "unbekannt"

    def rohnetz_erzeugen(self, klassen: set[str], massstab: int) -> tuple[trimesh.Trimesh, list[trimesh.Trimesh], int]:
        """Trianguliert alle Elemente der angegebenen Klassen.

        Rückgabe: (Rohnetz gesamt, Liste der Einzelnetze, Anzahl Fehler),
        alles im Modellmass [mm]. IfcOpenShell liefert Meter → ×1000.
        Die Einzelnetze braucht core/huelle.py für die Volumen-Voxelisierung.
        """
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)

        # by_type() liefert auch Unterklassen (IfcWall enthält IfcWallStandardCase)
        # → über die ID deduplizieren, sonst wird ein Bauteil doppelt trianguliert
        elemente = {e.id(): e for k in klassen for e in self.modell.by_type(k)}

        meshes, fehler = [], 0
        for element in elemente.values():
            try:
                shape = ifcopenshell.geom.create_shape(settings, element)
            except Exception:
                fehler += 1  # z.B. IfcRoof ohne eigene Geometrie (nur Container der Dachplatten)
                continue
            verts = np.array(shape.geometry.verts).reshape(-1, 3) * 1000 / massstab  # m → mm → Modell
            faces = np.array(shape.geometry.faces).reshape(-1, 3)
            if len(faces):
                meshes.append(trimesh.Trimesh(vertices=verts, faces=faces, process=False))

        if not meshes:
            raise ValueError("Keine Meshes erzeugt – IFC-Datei bzw. Klassenliste prüfen.")
        return trimesh.util.concatenate(meshes), meshes, fehler

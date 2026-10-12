"""M1 – IFC-Import und Bauteilanalyse.

Klasse IfcModell: lädt eine IFC-Datei, liefert eine Pandas-Tabelle aller
Bauteile (GUID, Klasse, Name, Geschoss) und trianguliert ausgewählte
Klassen zu einem Rohnetz.
Stufe 1 ergänzt: BBox und minimale Dicke pro Bauteil.
"""

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit
import multiprocessing
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

    def bauteile_laden(self, mit_geometrie: bool = True) -> pd.DataFrame:
        """Gibt DataFrame aller IfcProduct-Instanzen mit Darstellung zurück.

        Spalten: guid, klasse, name, geschoss sowie – bei mit_geometrie=True –
        die reale Bounding-Box bbox_x_mm / bbox_y_mm / bbox_z_mm (Massstab 1:1)
        und dicke_min_mm (kleinste BBox-Kante). Die realen mm rechnet
        core/druckbarkeit.modellmass() später auf den Modellmassstab um.
        Bauteile ohne auswertbare Geometrie erhalten NaN in den BBox-Spalten.
        """
        bbox = self._bbox_je_guid() if mit_geometrie else {}
        zeilen = []
        for element in self.modell.by_type("IfcProduct"):
            if not element.Representation:
                continue
            dx, dy, dz = bbox.get(element.GlobalId, (np.nan, np.nan, np.nan))
            zeilen.append({
                "guid":        element.GlobalId,
                "klasse":      element.is_a(),
                "name":        getattr(element, "Name", "") or "",
                "geschoss":    self.geschoss_fuer(element),
                "bbox_x_mm":   dx,
                "bbox_y_mm":   dy,
                "bbox_z_mm":   dz,
                "dicke_min_mm": np.nanmin([dx, dy, dz]) if mit_geometrie else np.nan,
            })
        self.bauteile_df = pd.DataFrame(zeilen)
        return self.bauteile_df

    def _bbox_je_guid(self) -> dict[str, tuple[float, float, float]]:
        """Liefert pro GUID die reale Bounding-Box (dx, dy, dz) in mm (1:1).

        Trianguliert alle Bauteile mit Geometrie einmalig über den Geom-Iterator.
        IfcOpenShell liefert Meter → ×1000 ergibt reale Millimeter.
        """
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)
        settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, True)

        it = ifcopenshell.geom.iterator(settings, self.modell, multiprocessing.cpu_count())
        result: dict[str, tuple[float, float, float]] = {}
        if it.initialize():
            while True:
                shape = it.get()
                verts = np.array(shape.geometry.verts).reshape(-1, 3)
                if len(verts):
                    dims = (verts.max(axis=0) - verts.min(axis=0)) * 1000
                    result[shape.guid] = (float(dims[0]), float(dims[1]), float(dims[2]))
                if not it.next():
                    break
        return result

    def geschosse_hoehen(self, massstab: int) -> list[tuple[str, float]]:
        """Gibt sortierte Liste (Name, Z_mm_im_Modell) aller IfcBuildingStorey zurück."""
        scale = ifcopenshell.util.unit.calculate_unit_scale(self.modell)  # Faktor → Meter
        result = []
        for s in self.modell.by_type("IfcBuildingStorey"):
            if s.Elevation is not None:
                z_m = float(s.Elevation) * scale
                result.append((s.Name or "unbekannt", z_m * 1000 / massstab))
        return sorted(result, key=lambda x: x[1])

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
        # Fenster/Tür-Ausschnitte weglassen: viele Wände scheitern sonst an booleschen Ops
        settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, True)

        # by_type() liefert auch Unterklassen (IfcWall enthält IfcWallStandardCase)
        # → über die ID deduplizieren, sonst wird ein Bauteil doppelt trianguliert
        elemente = {e.id(): e for k in klassen for e in self.modell.by_type(k)}
        # CLADDING-Verkleidungen ergänzen: werden in manchen IFC4-Dateien für Brüstungen genutzt
        for e in self.modell.by_type("IfcCovering"):
            if getattr(e, "PredefinedType", None) == "CLADDING":
                elemente[e.id()] = e

        # Iterator löst IfcMappedItem-Referenzen korrekt auf (create_shape scheitert daran)
        it = ifcopenshell.geom.iterator(settings, self.modell, multiprocessing.cpu_count(),
                                        include=list(elemente.values()))
        meshes, fehler = [], 0
        if it.initialize():
            while True:
                shape = it.get()
                verts = np.array(shape.geometry.verts).reshape(-1, 3) * 1000 / massstab
                faces = np.array(shape.geometry.faces).reshape(-1, 3)
                if len(faces):
                    meshes.append(trimesh.Trimesh(vertices=verts, faces=faces, process=False))
                if not it.next():
                    break

        if not meshes:
            raise ValueError("Keine Meshes erzeugt – IFC-Datei bzw. Klassenliste prüfen.")
        return trimesh.util.concatenate(meshes), meshes, fehler

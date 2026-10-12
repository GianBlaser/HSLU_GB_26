"""M6 – Kalkulation: Filament, Kosten, Druckzeit (Schätzung)."""

from config import MATERIAL_DICHTE_G_CM3, MATERIAL_PREIS_CHF_KG, VOLUMEN_FAKTOR, LAYER_HOEHE_MM


def filament_gramm(volumen_cm3: float) -> float:
    """Berechnet das Filamentgewicht in Gramm (vereinfacht mit Volumenfaktor)."""
    return volumen_cm3 * VOLUMEN_FAKTOR * MATERIAL_DICHTE_G_CM3


def kosten_chf(gramm: float) -> float:
    """Berechnet die Materialkosten in CHF."""
    return gramm / 1000 * MATERIAL_PREIS_CHF_KG


def druckzeit_stunden(volumen_cm3: float, hoehe_mm: float, durchsatz_cm3_h: float = 10.0) -> float:
    """Schätzt die Druckzeit in Stunden (als Schätzung deklarieren!)."""
    anzahl_layer = hoehe_mm / LAYER_HOEHE_MM
    layer_zuschlag_h = anzahl_layer * 0.001  # empirisch kalibrieren
    return volumen_cm3 * VOLUMEN_FAKTOR / durchsatz_cm3_h + layer_zuschlag_h

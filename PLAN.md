# IFC2Print – Implementierungsplan

**Stand:** 12.10.2026  
**Nächste Deadline:** ZP1 Mo 26.10.2026 (Konzept + Umgebung präsentieren)  
**Go/No-Go Stufe 0:** ✅ GO (erreicht 12.10.2026 – wasserdichtes Modell)

---

## Stufe 0 – Machbarkeit ✅ ABGESCHLOSSEN (12.10.2026)

Machbarkeit nachgewiesen: Pipeline IFC → Rohnetz → Voxel-Hülle → **wasserdichtes STL** läuft durch.
Snapshot gesichert unter `_snapshots/stufe0_abschluss/`.

- [x] Projektstruktur + venv einrichten
- [x] `scripts/stufe0_machbarkeit.py` – IFC → Rohnetz → Voxel-Hülle → STL
- [x] Wasserdichtigkeit fix (np.pad + binary_fill_holes)
- [x] Wasserdichtes Modell erzeugt und verifiziert → **Go/No-Go: GO**
- [x] Snapshot `_snapshots/stufe0_abschluss/` angelegt

**Nachlauf (optional, nicht blockierend für Stufe 1):**
- [ ] NEST-Datei `ARC_Modell_NEST_230328.ifc` vom Dozenten besorgen → in `testdaten/` ablegen
- [ ] Skript mit echter NEST-Datei gegenprüfen, Messwerte in README ergänzen
- [ ] STL in PrusaSlicer/3D-Viewer öffnen, Screenshot → `docs/stufe0_prusaslicer.png`

**Aktuelles Testmodell:** `testdaten/Building-Architecture-IFC2x3.ifc` (IFC-Zertifizierungsdatei, IFC2x3)

---

## Klassifizierungsentscheid

**Gewählt: Option 2 – IFC-Klassen direkt nutzen** (kein eBKP-H erforderlich)

Bauteile werden über ihre IFC-Klasse gefiltert und kategorisiert:

| IFC-Klasse | Bedeutung | Drucken? |
|---|---|---|
| IfcWall, IfcWallStandardCase | Wand | Ja |
| IfcSlab | Decke / Bodenplatte | Ja |
| IfcRoof | Dach | Ja |
| IfcColumn | Stütze | Ja |
| IfcBeam | Träger | Ja |
| IfcCurtainWall | Vorhangfassade (NEST: Verglasung) | Nein (Toggle) |
| IfcPlate, IfcMember | Glasfüllung NEST | Nein (Toggle) |
| IfcDoor, IfcWindow | Öffnungen | Nein (Loch lassen) |

Vorteil: funktioniert mit allen IFC-Dateien ohne Schweizer Klassifizierung.  
eBKP-H-Datei (`docs/eBKP-H-Tandem.xlsx`) bleibt als Referenz vorhanden, wird aber nicht im Code verwendet.

---

## Stufe 1 – MVP (bis ZP1, 26.10)

### M1 – `core/ifc_modell.py` ✅
- [x] `bauteile_laden()`: alle IfcProduct mit Darstellung → DataFrame (guid, klasse, name, geschoss, bbox_x/y/z_mm, dicke_min_mm)
- [x] Unit-Test in `tests/test_ifc_modell.py`

### M2 – `core/regelwerk.py` ✅
- [x] Regelwerk fix (Python-Dict) + `KATEGORIEN`-Mapping je IFC-Klasse
- [x] Methode `klassifizieren(df)` → Spalten `aktion`, `drucken`, `kategorie` anfügen
- [x] Bestehender Test `tests/test_regelwerk.py` grün (+ neue Tests)

### M3 – `core/druckbarkeit.py` ✅
- [x] `status_spalte_hinzufuegen(df, massstab)`: Mindestdicke prüfen (Massstab × 0.8 mm Düse)
- [x] Bounding-Box-Volumen + Bauraum-Check

### Streamlit-App `app.py` ✅
- [x] IFC-Datei hochladen
- [x] Massstab wählen (1:50 / 1:100 / 1:200)
- [x] Bauteil-Tabelle anzeigen (kategorie, klasse, geschoss, dicke, status, drucken)
- [x] Download-Button für STL (Stufe-0-Pipeline: rohnetz_erzeugen → huelle_erzeugen)

---

## Stufe 2 (KW47–48, nach ZP1)
- Regelwerk in SQLite auslagern (`db/`)
- PDF-Report
- Fensterfüllung-Toggle in UI

## Stufe 3 (KW49–50)
- Geschossweise Aufteilung
- Steckverbinder
- 3MF-Export

---

## Offene Punkte
- NEST IFC-Datei besorgen (Dozent / Kursunterlagen)
- eBKP-H bleibt offen – nicht im Code, nur als Referenzdokument

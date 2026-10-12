# IFC2Print – Implementierungsplan

**Stand:** 08.10.2026  
**Nächste Deadline:** ZP1 Mo 26.10.2026 (Konzept + Umgebung präsentieren)  
**Go/No-Go Stufe 0:** 18.10.2026

---

## Stufe 0 – Machbarkeit (bis 18.10) ✅ Pipeline läuft

- [x] Projektstruktur + venv einrichten
- [x] `scripts/stufe0_machbarkeit.py` – IFC → Rohnetz → Voxel-Hülle → STL
- [x] Wasserdichtigkeit fix (np.pad + binary_fill_holes)
- [ ] NEST-Datei `ARC_Modell_NEST_230328.ifc` vom Dozenten besorgen → in `testdaten/` ablegen
- [ ] Skript mit echter NEST-Datei ausführen, Messwerte in README eintragen
- [ ] STL in PrusaSlicer/3D-Viewer öffnen, Screenshot → `docs/stufe0_prusaslicer.png`
- [ ] Go/No-Go in README eintragen

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

### M1 – `core/ifc_modell.py`
- [ ] `bauteile_laden()` implementieren: alle IfcProduct mit Darstellung → DataFrame (guid, klasse, name, geschoss, bbox)
- [ ] Unit-Test in `tests/test_ifc_modell.py`

### M2 – `core/regelwerk.py`
- [ ] Regelwerk fix (Python-Dict): IFC-Klasse → {drucken: bool, farbe: str}
- [ ] Methode `klassifizieren(df)` → Spalten `drucken`, `kategorie` anfügen
- [ ] Bestehender Test `tests/test_regelwerk.py` grün bringen

### M3 – `core/druckbarkeit.py`
- [ ] Mindestdicke prüfen (Massstab × 0.8 mm Düse = Schwellwert)
- [ ] Bounding-Box-Volumen berechnen

### Streamlit-App `app.py`
- [ ] IFC-Datei hochladen
- [ ] Massstab wählen (1:50 / 1:100 / 1:200)
- [ ] Bauteil-Tabelle anzeigen (klasse, geschoss, drucken Ja/Nein)
- [ ] Einfacher Download-Button für STL (Stufe 0-Pipeline aufrufen)

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

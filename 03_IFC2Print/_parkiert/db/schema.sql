-- IFC2Print Datenbankschema (Stufe 2)

CREATE TABLE IF NOT EXISTS drucker_profil (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    duese_mm    REAL NOT NULL,
    layer_mm    REAL NOT NULL,
    bauraum_x   REAL NOT NULL,
    bauraum_y   REAL NOT NULL,
    bauraum_z   REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS material (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    dichte_g_cm3 REAL NOT NULL,
    preis_chf_kg REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS regel (
    id          INTEGER PRIMARY KEY,
    regelset    TEXT NOT NULL,
    ifc_klasse  TEXT NOT NULL,
    aktion      TEXT NOT NULL,   -- entfernen | verdicken | behalten | fuellen
    parameter_json TEXT          -- z.B. {"min_dicke_mm": 0.8}
);

CREATE TABLE IF NOT EXISTS exportlauf (
    id              INTEGER PRIMARY KEY,
    datum           TEXT NOT NULL,
    ifc_name        TEXT NOT NULL,
    massstab        INTEGER NOT NULL,
    profil_id       INTEGER REFERENCES drucker_profil(id),
    regelset        TEXT NOT NULL,
    modus           TEXT NOT NULL,  -- ein_stueck | geschossweise
    fenster_fuellen INTEGER NOT NULL DEFAULT 0,
    anzahl_teile    INTEGER,
    filament_g      REAL,
    zeit_h          REAL,
    kosten_chf      REAL
);

"""Zentrale Defaultwerte für IFC2Print (Stufe 0–3)."""

# Druckerprofil (Prusa MK4, 0.4-mm-Düse)
DUESE_MM = 0.4
LAYER_HOEHE_MM = 0.2
BAURAUM_X_MM = 250.0
BAURAUM_Y_MM = 210.0
BAURAUM_Z_MM = 220.0

# Druckbarkeits-Schwellwerte (Modellmass in mm)
MINDESTWAND_MM = 0.8       # ≥ 2 Linien → sicher druckbar
KRITISCH_BIS_MM = 1.2      # 0.8–1.2 mm → druckbar, aber fragil

# Voxelisierung
VOXEL_PITCH_MM = MINDESTWAND_MM / 2  # = 0.4 mm

# Massstab
MASSSTAB_DEFAULT = 200     # 1:200
MASSSTAB_MIN = 50
MASSSTAB_MAX = 1000

# Steckverbinder
ZAPFEN_DURCHMESSER_MM = 3.0
ZAPFEN_HOEHE_MM = 3.0
ZAPFEN_TOLERANZ_MM = 0.2   # Loch-Ø = ZAPFEN_DURCHMESSER_MM + 2 * TOLERANZ

# Bodenplatte
BODENPLATTE_DICKE_MM = 1.6

# Material (PLA)
MATERIAL_DICHTE_G_CM3 = 1.24
MATERIAL_PREIS_CHF_KG = 25.0

# Füllgrad (Schätzung)
VOLUMEN_FAKTOR = 0.4       # vereinfachter Füllfaktor inkl. Wände

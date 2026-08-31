from pydantic import BaseModel, Field


class BBox(BaseModel):
    north: float = Field(..., ge=-90, le=90)
    south: float = Field(..., ge=-90, le=90)
    east: float = Field(..., ge=-180, le=180)
    west: float = Field(..., ge=-180, le=180)


MERCH_SPECS = {
    # bleed_mm: print-area extension past the trimmed edge so the cut leaves no white halo.
    # 0 means the user's selection runs edge-to-edge; 3 mm is the typical offset/digital default.
    "placemat":  {"ratio_x": 14, "ratio_y": 10, "dpi": 300, "width_px": 4200, "height_px": 3000, "bleed_mm": 3.0},
    "coaster":   {"ratio_x":  1, "ratio_y":  1, "dpi": 300, "width_px": 1000, "height_px": 1000, "bleed_mm": 3.0},
    "tshirt":    {"ratio_x":  3, "ratio_y":  4, "dpi": 300, "width_px": 3000, "height_px": 4000, "bleed_mm": 3.0},
    "mug":       {"ratio_x":  9, "ratio_y":  3, "dpi": 300, "width_px": 2700, "height_px":  900, "bleed_mm": 0.0},
    "tote":      {"ratio_x":  2, "ratio_y":  3, "dpi": 300, "width_px": 2000, "height_px": 3000, "bleed_mm": 3.0},
    "3d_print":  {"ratio_x":  1, "ratio_y":  1, "dpi": 150, "width_px":  800, "height_px":  800, "bleed_mm": 0.0},
}


class SVGGenerationRequest(BaseModel):
    bbox: BBox
    merch_type: str = Field(
        ..., pattern="^(placemat|coaster|tshirt|mug|tote|3d_print)$"
    )
    style: str = "osm_default"
    include_labels: bool = True
    include_buildings: bool = True
    include_roads: bool = True
    include_parks: bool = True
    coaster_shape: str = "square"           # 'square' | 'circle' | 'hexagon'
    palette_overrides: dict[str, str] = {}  # per-category hex colour overrides
    # Override the merch spec's bleed (mm per side). None → use the spec default.
    bleed_mm: float | None = None


class STLGenerationRequest(BaseModel):
    bbox: BBox
    merch_type: str = "3d_print"
    coaster_shape: str = "square"   # 'square' | 'circle' | 'hexagon'
    # Layer heights (mm) — equal thirds so assembled coaster is flat-topped
    bldg_height: float = 4.0             # total height; buildings poke full height
    water_start: float = 4.0 / 3        # ≈ 1.333 mm
    water_end:   float = 4.0 * 2 / 3   # ≈ 2.667 mm
    land_start:  float = 4.0 * 2 / 3   # ≈ 2.667 mm (= water_end, flat-top)
    land_end:    float = 4.0            # = bldg_height
    # Geometry processing
    gap_close_mm:    float = 0.8   # merge buildings with gap < this
    water_expand_mm: float = 0.5   # expand water bodies by this amount
    min_bldg_mm:     float = 1.0   # minimum building height
    collar_mm:       float = 1.0   # outer collar width on base + lid
    # Moat text — branding carved through land, surrounded by blue water
    moat_text: str | None = None
    moat_position: str = "bottom"  # top/bottom[-left|-right] — mirrors the SVG stamp position
    moat_style: str = "outline"    # outline | banner — mirrors the SVG stamp style
    # Legacy (ignored — kept for backward compat with old callers)
    height_mm: float = 4.0
    base_thickness_mm: float = 2.0


class LicenseCheckRequest(BaseModel):
    bbox: BBox
    data_sources: list[str]  # e.g. ["osm", "nasa_srtm", "custom_upload"]

"""Generate reproducible synthetic thematic rasters for testing.

These are artificial suitability scores, not observed geological data.
"""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin


OUTPUT_DIR = Path("data/demo")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SIZE = 100
RANDOM_SEED = 42

rng = np.random.default_rng(RANDOM_SEED)

# Synthetic grid: EPSG:32645, 30 m pixels.
# Coordinates are illustrative and do not represent a surveyed site.
transform = from_origin(500000, 2500000, 30, 30)

x = np.linspace(0, 1, SIZE)
y = np.linspace(0, 1, SIZE)
xx, yy = np.meshgrid(x, y)

# A synthetic spatial suitability pattern.
base = (
    2.5
    + 1.2 * np.sin(xx * np.pi)
    + 0.8 * np.cos(yy * np.pi)
)

def make_scores(signal, noise=0.45):
    """Convert an artificial continuous signal into scores 1–5."""
    values = signal + rng.normal(0, noise, (SIZE, SIZE))
    return np.clip(np.rint(values), 1, 5).astype(np.uint8)


rasters = {
    "geology.tif": make_scores(base + 0.5),
    "slope.tif": make_scores(4.0 - base * 0.5),
    "drainage_density.tif": make_scores(base - 0.2),
    "lineament_density.tif": make_scores(base + 0.2),
    "rainfall.tif": make_scores(base),
}

profile = {
    "driver": "GTiff",
    "height": SIZE,
    "width": SIZE,
    "count": 1,
    "dtype": "uint8",
    "crs": "EPSG:32645",
    "transform": transform,
    "nodata": 0,
    "compress": "deflate",
}

for filename, array in rasters.items():
    path = OUTPUT_DIR / filename

    with rasterio.open(path, "w", **profile) as dst:
        dst.write(array, 1)
        dst.set_band_description(
            1,
            "Synthetic groundwater suitability score (1–5)",
        )
        dst.update_tags(
            DATA_TYPE="SYNTHETIC DEMONSTRATION DATA",
            SCORE_SCALE="1=Very Low, 5=Very High",
            NOT_REAL_OBSERVATIONS="True",
        )

    print(f"Created: {path}")

print("\nSynthetic thematic raster generation complete.")
print(f"Raster dimensions: {SIZE} x {SIZE}")
print("CRS: EPSG:32645")

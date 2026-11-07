
"""Run the synthetic groundwater potential demonstration."""

from pathlib import Path

from src.overlay import calculate_weighted_overlay


raster_paths = {
    "Geology": "data/demo/geology.tif",
    "Slope": "data/demo/slope.tif",
    "Drainage Density": "data/demo/drainage_density.tif",
    "Lineament Density": "data/demo/lineament_density.tif",
    "Rainfall": "data/demo/rainfall.tif",
}

# Demonstration weights from the earlier AHP dashboard.
# These are illustrative judgments, not validated study weights.
weights = {
    "Geology": 0.4388,
    "Slope": 0.1396,
    "Drainage Density": 0.1280,
    "Lineament Density": 0.1396,
    "Rainfall": 0.1540,
}

result = calculate_weighted_overlay(
    raster_paths=raster_paths,
    weights=weights,
    gwpi_output="outputs/groundwater_potential_index.tif",
    classes_output="outputs/groundwater_potential_zones.tif",
)

print("\nGROUNDWATER POTENTIAL DEMONSTRATION")
print("----------------------------------")
print(f"Valid pixels: {result['valid_pixels']}")
print(f"GWPI raster: {result['gwpi_output']}")
print(f"Zone raster: {result['classes_output']}")

print("\nAHP weights:")
for name, weight in result["weights"].items():
    print(f"{name}: {weight:.2%}")

print("\nDemonstration completed successfully.")

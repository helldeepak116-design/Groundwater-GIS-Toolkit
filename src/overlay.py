
"""Weighted overlay analysis for groundwater potential mapping.

Input rasters must contain standardized suitability scores:
1 = Very Low, 2 = Low, 3 = Moderate, 4 = High, 5 = Very High.
All rasters must share an identical spatial grid.
"""

from pathlib import Path

import numpy as np
import rasterio


NODATA_FLOAT = -9999.0
NODATA_CLASS = 0

CLASS_NAMES = {
    1: "Very Low",
    2: "Low",
    3: "Moderate",
    4: "High",
    5: "Very High",
}


def validate_inputs(raster_paths, weights):
    """Validate raster paths and AHP weights."""

    if not raster_paths:
        raise ValueError("At least one input raster is required.")

    if set(raster_paths) != set(weights):
        raise ValueError(
            "Raster names and weight names must match exactly."
        )

    weight_values = np.asarray(list(weights.values()), dtype=float)

    if not np.all(np.isfinite(weight_values)):
        raise ValueError("Weights must be finite numbers.")

    if np.any(weight_values <= 0):
        raise ValueError("All weights must be positive.")

    if not np.isclose(weight_values.sum(), 1.0, atol=1e-6):
        raise ValueError("AHP weights must sum to 1.")

    for name, path in raster_paths.items():
        if not Path(path).is_file():
            raise FileNotFoundError(
                f"Raster not found for {name}: {path}"
            )


def calculate_weighted_overlay(
    raster_paths,
    weights,
    gwpi_output="outputs/groundwater_potential_index.tif",
    classes_output="outputs/groundwater_potential_zones.tif",
):
    """Calculate GWPI and classify groundwater potential.

    Returns
    -------
    dict
        Output paths, normalized weights and valid pixel count.
    """

    validate_inputs(raster_paths, weights)

    names = list(raster_paths.keys())

    normalized_weights = {
        name: float(weights[name]) for name in names
    }

    reference = None
    raster_arrays = []
    valid_masks = []

    # Read and validate all input rasters.
    for name in names:
        with rasterio.open(raster_paths[name]) as src:

            if src.count < 1:
                raise ValueError(f"{name} has no raster bands.")

            if src.crs is None:
                raise ValueError(f"{name} has no CRS.")

            if reference is None:
                reference = {
                    "crs": src.crs,
                    "transform": src.transform,
                    "width": src.width,
                    "height": src.height,
                    "profile": src.profile.copy(),
                }

            else:
                if src.crs != reference["crs"]:
                    raise ValueError(
                        f"CRS mismatch in raster: {name}"
                    )

                if src.width != reference["width"]:
                    raise ValueError(
                        f"Width mismatch in raster: {name}"
                    )

                if src.height != reference["height"]:
                    raise ValueError(
                        f"Height mismatch in raster: {name}"
                    )

                if src.transform != reference["transform"]:
                    raise ValueError(
                        f"Grid alignment mismatch in raster: {name}"
                    )

            data = src.read(1, masked=True).astype(np.float32)

            values = data.compressed()

            if not np.all(np.isfinite(values)):
                raise ValueError(
                    f"{name} contains invalid unmasked values."
                )

            if np.any((values < 1) | (values > 5)):
                raise ValueError(
                    f"{name} must contain suitability scores from 1 to 5."
                )

            raster_arrays.append(data.filled(np.nan))
            valid_masks.append(~np.ma.getmaskarray(data))

    # A pixel is valid only if every thematic layer is valid.
    common_mask = np.logical_and.reduce(valid_masks)

    if not np.any(common_mask):
        raise ValueError("No common valid pixels across input rasters.")

    # Calculate Groundwater Potential Index.
    gwpi = np.full(
        common_mask.shape,
        NODATA_FLOAT,
        dtype=np.float32,
    )
    
    gwpi[common_mask] = 0.0

    for name, array in zip(names, raster_arrays):
        gwpi[common_mask] += (
            array[common_mask] * normalized_weights[name]
        )

    # Classify the index into five equal-width score intervals.
    classified = np.full(
        common_mask.shape,
        NODATA_CLASS,
        dtype=np.uint8,
    )

    thresholds = [1.8, 2.6, 3.4, 4.2]

    classified[common_mask] = (
        np.digitize(
            gwpi[common_mask],
            thresholds,
            right=False,
        ) + 1
    ).astype(np.uint8)

    # Prepare output directories.
    gwpi_path = Path(gwpi_output)
    classes_path = Path(classes_output)

    gwpi_path.parent.mkdir(parents=True, exist_ok=True)
    classes_path.parent.mkdir(parents=True, exist_ok=True)

    base_profile = reference["profile"]

    # Write continuous GWPI raster.
    gwpi_profile = base_profile.copy()
    gwpi_profile.update(
        dtype="float32",
        count=1,
        nodata=NODATA_FLOAT,
        compress="deflate",
    )

    with rasterio.open(gwpi_path, "w", **gwpi_profile) as dst:
        dst.write(gwpi, 1)
        dst.set_band_description(1, "Groundwater Potential Index")

    # Write classified groundwater potential raster.
    class_profile = base_profile.copy()
    class_profile.update(
        dtype="uint8",
        count=1,
        nodata=NODATA_CLASS,
        compress="deflate",
    )

    with rasterio.open(classes_path, "w", **class_profile) as dst:
        dst.write(classified, 1)
        dst.set_band_description(1, "Groundwater Potential Zones")

        dst.update_tags(
            1,
            CLASS_1="Very Low",
            CLASS_2="Low",
            CLASS_3="Moderate",
            CLASS_4="High",
            CLASS_5="Very High",
            CLASSIFICATION="Equal-width intervals from 1 to 5",
        )

    return {
        "gwpi_output": str(gwpi_path),
        "classes_output": str(classes_path),
        "weights": normalized_weights,
        "valid_pixels": int(common_mask.sum()),
        "classification": CLASS_NAMES,
    }

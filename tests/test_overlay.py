
import numpy as np
import rasterio
import pytest

from rasterio.transform import from_origin
from src.overlay import calculate_weighted_overlay


def create_test_raster(path, data, nodata=-9999):
    profile = {
        "driver": "GTiff",
        "height": data.shape[0],
        "width": data.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:32645",
        "transform": from_origin(500000, 2500000, 30, 30),
        "nodata": nodata,
    }

    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data.astype("float32"), 1)


def test_weighted_overlay_calculation(tmp_path):
    geology = np.array([[1, 2], [3, 4]], dtype=float)
    slope = np.array([[5, 4], [3, 2]], dtype=float)

    geology_path = tmp_path / "geology.tif"
    slope_path = tmp_path / "slope.tif"

    create_test_raster(geology_path, geology)
    create_test_raster(slope_path, slope)

    result = calculate_weighted_overlay(
        {"Geology": geology_path, "Slope": slope_path},
        {"Geology": 0.5, "Slope": 0.5},
        gwpi_output=tmp_path / "gwpi.tif",
        classes_output=tmp_path / "zones.tif",
    )

    assert result["valid_pixels"] == 4

    with rasterio.open(tmp_path / "gwpi.tif") as src:
        output = src.read(1)

    assert np.allclose(output, 3.0)


def test_nodata_intersection(tmp_path):
    geology = np.array([
        [1, -9999],
        [3, 4],
    ], dtype=float)

    slope = np.array([
        [5, 4],
        [3, 2],
    ], dtype=float)

    geology_path = tmp_path / "geology.tif"
    slope_path = tmp_path / "slope.tif"

    create_test_raster(geology_path, geology)
    create_test_raster(slope_path, slope)

    result = calculate_weighted_overlay(
        {"Geology": geology_path, "Slope": slope_path},
        {"Geology": 0.5, "Slope": 0.5},
        gwpi_output=tmp_path / "gwpi.tif",
        classes_output=tmp_path / "zones.tif",
    )

    assert result["valid_pixels"] == 3

    with rasterio.open(tmp_path / "gwpi.tif") as src:
        output = src.read(1)

    assert output[0, 1] == -9999
    assert np.isclose(output[0, 0], 3.0)


def test_rejects_weights_not_summing_to_one(tmp_path):
    geology_path = tmp_path / "geology.tif"
    slope_path = tmp_path / "slope.tif"

    create_test_raster(geology_path, np.ones((2, 2)))
    create_test_raster(slope_path, np.ones((2, 2)))

    with pytest.raises(ValueError, match="sum to 1"):
        calculate_weighted_overlay(
            {"Geology": geology_path, "Slope": slope_path},
            {"Geology": 0.4, "Slope": 0.4},
            gwpi_output=tmp_path / "gwpi.tif",
            classes_output=tmp_path / "zones.tif",
        )

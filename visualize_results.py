
"""Create a publication-style groundwater potential map."""

from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import matplotlib.pyplot as plt

from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from rasterio.plot import plotting_extent


INPUT = Path("outputs/groundwater_potential_zones.tif")
OUTPUT_DIR = Path("outputs")

MAP_OUTPUT = OUTPUT_DIR / "groundwater_potential_map.png"
STATS_OUTPUT = OUTPUT_DIR / "groundwater_zone_statistics.csv"

CLASS_NAMES = {
    1: "Very Low",
    2: "Low",
    3: "Moderate",
    4: "High",
    5: "Very High",
}

# Cartographic colors: low potential to high potential.
COLORS = [
    "#d73027",
    "#fc8d59",
    "#fee08b",
    "#91cf60",
    "#1a9850",
]


def main():
    if not INPUT.is_file():
        raise FileNotFoundError(
            f"Classification raster not found: {INPUT}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with rasterio.open(INPUT) as src:
        if src.crs is None:
            raise ValueError("Input raster has no CRS.")

        if not src.crs.is_projected:
            raise ValueError(
                "A projected CRS is required for area and scale calculations."
            )

        data = src.read(1, masked=True)
        transform = src.transform
        crs = src.crs
        extent = plotting_extent(src)
        width = src.width
        height = src.height

        # Convert map units to metres.
        from pyproj import CRS as PyprojCRS
        projected_crs = PyprojCRS.from_user_input(crs)

        if not projected_crs.is_projected:
            raise ValueError("A projected CRS is required.")
        
        axis_info = projected_crs.axis_info
        
        if not axis_info:
            raise ValueError("Could not determine CRS axis information.")
        
        unit_factor = axis_info[0].unit_conversion_factor
        
        if unit_factor is None or unit_factor <= 0:
            raise ValueError("Could not determine CRS linear units.")
        

        pixel_area_m2 = abs(
            transform.a * transform.e
            - transform.b * transform.d
        ) * unit_factor**2

    valid = ~np.ma.getmaskarray(data)
    values = np.asarray(data.data)

    if not np.any(valid):
        raise ValueError("Classification raster has no valid pixels.")

    observed = set(np.unique(values[valid]).tolist())

    if not observed.issubset(set(CLASS_NAMES)):
        raise ValueError(
            f"Unexpected class values found: {observed}"
        )

    # Calculate area statistics.
    rows = []

    for class_id, class_name in CLASS_NAMES.items():
        count = int(np.count_nonzero(valid & (values == class_id)))
        area_ha = count * pixel_area_m2 / 10000

        rows.append({
            "Class": class_id,
            "Potential Zone": class_name,
            "Pixel Count": count,
            "Area (ha)": area_ha,
            "Area (%)": count / valid.sum() * 100,
        })

    stats = pd.DataFrame(rows)
    stats.to_csv(STATS_OUTPUT, index=False)

    # Create map.
    cmap = ListedColormap(COLORS)
    norm = BoundaryNorm(
        np.arange(0.5, 6.0, 1.0),
        cmap.N,
    )

    fig, ax = plt.subplots(figsize=(12, 10))

    ax.imshow(
        np.ma.masked_where(~valid, values),
        cmap=cmap,
        norm=norm,
        extent=extent,
        origin="upper",
        interpolation="nearest",
    )

    ax.set_title(
        "GROUNDWATER POTENTIAL ZONATION MAP",
        fontsize=17,
        fontweight="bold",
        pad=20,
    )

    ax.set_xlabel(f"Easting ({axis_info[0].unit_name})")
    ax.set_ylabel(f"Northing ({axis_info[1].unit_name})")

    ax.ticklabel_format(
        style="plain",
        axis="both",
        useOffset=False,
    )

    # North arrow.
    ax.annotate(
        "N",
        xy=(0.93, 0.92),
        xytext=(0.93, 0.82),
        xycoords="axes fraction",
        textcoords="axes fraction",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        arrowprops={
            "arrowstyle": "-|>",
            "linewidth": 2,
            "color": "black",
        },
    )

    # Scale bar in metres, with a rounded length.
    map_width_m = abs(extent[1] - extent[0]) * unit_factor
    target = map_width_m / 5

    magnitude = 10 ** np.floor(np.log10(target))
    normalized = target / magnitude

    if normalized >= 5:
        scale_length_m = 5 * magnitude
    elif normalized >= 2:
        scale_length_m = 2 * magnitude
    else:
        scale_length_m = magnitude

    scale_length_units = scale_length_m / unit_factor

    x_start = extent[0] + (extent[1] - extent[0]) * 0.08
    y_start = extent[2] + (extent[3] - extent[2]) * 0.08

    ax.plot(
        [x_start, x_start + scale_length_units],
        [y_start, y_start],
        color="black",
        linewidth=4,
        solid_capstyle="butt",
    )

    ax.text(
        x_start + scale_length_units / 2,
        y_start + (extent[3] - extent[2]) * 0.025,
        f"{scale_length_m / 1000:g} km",
        ha="center",
        fontsize=10,
        fontweight="bold",
    )

    # Legend.
    legend_items = [
        Patch(
            facecolor=COLORS[i - 1],
            edgecolor="black",
            label=f"{i} — {CLASS_NAMES[i]}",
        )
        for i in CLASS_NAMES
    ]

    ax.legend(
        handles=legend_items,
        title="Groundwater Potential",
        loc="upper left",
        frameon=True,
        fontsize=10,
    )

    ax.set_aspect("equal")
    ax.grid(
        True,
        linestyle="--",
        alpha=0.3,
        linewidth=0.5,
    )

    fig.text(
        0.5,
        0.025,
        f"CRS: {crs} | Pixel size: "
        f"{abs(transform.a) * unit_factor:g} m | "
        "Synthetic demonstration data",
        ha="center",
        fontsize=9,
    )

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(
        MAP_OUTPUT,
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)

    print("\nMAP VISUALIZATION COMPLETE")
    print("--------------------------")
    print(f"Map: {MAP_OUTPUT}")
    print(f"Statistics: {STATS_OUTPUT}")
    print(f"CRS: {crs}")
    print(f"Valid pixels: {int(valid.sum())}")

    print("\nGROUNDWATER POTENTIAL AREA STATISTICS")
    print(stats.to_string(index=False))


if __name__ == "__main__":
    main()


"""Streamlit interface for Groundwater GIS Toolkit."""

import numpy as np
import pandas as pd
import streamlit as st

from src.ahp import calculate_ahp


st.set_page_config(
    page_title="Groundwater GIS Toolkit",
    page_icon="🌍",
    layout="wide",
)

st.title("🌍 Groundwater Potential Analysis")
st.caption("Analytic Hierarchy Process (AHP) — Decision Support Tool")

st.markdown(
    "Calculate criterion weights using pairwise comparisons "
    "and evaluate the consistency of your geological judgments."
)

st.divider()

# --------------------------------------------------
# 1. Criteria configuration
# --------------------------------------------------

st.subheader("1. Define geological criteria")

default_criteria = [
    "Geology",
    "Slope",
    "Drainage Density",
    "Lineament Density",
    "Rainfall",
]

criteria = []

cols = st.columns(5)

for i, default_name in enumerate(default_criteria):
    with cols[i]:
        name = st.text_input(
            f"Criterion {i + 1}",
            value=default_name,
            key=f"criterion_{i}",
        )
        criteria.append(name.strip())

if any(not name for name in criteria):
    st.error("Criterion names cannot be empty.")
    st.stop()

if len(set(criteria)) != len(criteria):
    st.error("Criterion names must be unique.")
    st.stop()

# --------------------------------------------------
# 2. Pairwise comparison matrix
# --------------------------------------------------

st.subheader("2. Pairwise comparison")

st.info(
    "Enter how strongly the row criterion is preferred "
    "over the column criterion. A value of 1 means equal "
    "importance; 3 means moderate importance; 5 means "
    "strong importance; 7 means very strong importance; "
    "9 means extreme importance. Intermediate values "
    "are also permitted."
)

n = len(criteria)
matrix = np.ones((n, n), dtype=float)

with st.container(border=True):
    for i in range(n):
        for j in range(i + 1, n):
            left, right = st.columns([2, 3])

            with left:
                st.write(
                    f"**{criteria[i]}** vs **{criteria[j]}**"
                )

            with right:
                value = st.number_input(
                    f"Comparison: {criteria[i]} / {criteria[j]}",
                    min_value=1 / 9,
                    max_value=9.0,
                    value=1.0,
                    step=0.1,
                    format="%.3f",
                    key=f"comparison_{i}_{j}",
                    label_visibility="collapsed",
                )

            matrix[i, j] = value
            matrix[j, i] = 1.0 / value

st.write("**Generated reciprocal comparison matrix**")

matrix_df = pd.DataFrame(
    matrix,
    index=criteria,
    columns=criteria,
)

st.dataframe(
    matrix_df.style.format("{:.3f}"),
    use_container_width=True,
)

# --------------------------------------------------
# 3. Calculate AHP
# --------------------------------------------------

st.divider()
st.subheader("3. Calculate criterion weights")

if st.button(
    "Calculate AHP Weights",
    type="primary",
    use_container_width=True,
):

    try:
        result = calculate_ahp(
            matrix,
            criteria=criteria,
            threshold=0.10,
        )

        st.session_state["ahp_result"] = result
        st.session_state["ahp_matrix"] = matrix_df

    except (ValueError, np.linalg.LinAlgError) as error:
        st.error(f"Calculation error: {error}")

# --------------------------------------------------
# 4. Display results
# --------------------------------------------------

if "ahp_result" in st.session_state:

    result = st.session_state["ahp_result"]

    st.divider()
    st.subheader("4. AHP Results")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Maximum Eigenvalue",
        f"{result.lambda_max:.4f}",
    )

    col2.metric(
        "Consistency Index (CI)",
        f"{result.consistency_index:.4f}",
    )

    col3.metric(
        "Consistency Ratio (CR)",
        f"{result.consistency_ratio:.4f}",
    )

    if result.is_consistent:
        st.success(
            "Consistency acceptable: CR ≤ 0.10"
        )
    else:
        st.warning(
            "Consistency unacceptable: CR > 0.10. "
            "Review your pairwise judgments."
        )

    results_df = pd.DataFrame({
        "Criterion": result.criteria,
        "Weight": result.weights,
        "Weight (%)": result.weights * 100,
    })

    results_df = results_df.sort_values(
        "Weight",
        ascending=False,
    )

    st.subheader("Criterion weights")

    st.dataframe(
        results_df.style.format({
            "Weight": "{:.4f}",
            "Weight (%)": "{:.2f}%",
        }),
        use_container_width=True,
    )

    st.subheader("Weight distribution")

    chart_df = results_df.set_index("Criterion")[["Weight (%)"]]

    st.bar_chart(chart_df)

    # --------------------------------------------------
    # 5. Export
    # --------------------------------------------------

    csv_data = results_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download AHP Results (CSV)",
        data=csv_data,
        file_name="ahp_criterion_weights.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.caption(
        "Note: AHP weights represent relative judgment-based "
        "importance. They do not independently establish "
        "groundwater potential or validate the input data."
    )

st.divider()

st.caption(
    "Groundwater-GIS-Toolkit | Open-source scientific project"
)

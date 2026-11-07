
"""Analytic Hierarchy Process (AHP) calculations.

Implements eigenvector-derived criterion weights and the
Saaty Consistency Ratio for pairwise comparison matrices.
"""

from dataclasses import dataclass

import numpy as np


# Saaty's Random Index values
RANDOM_INDEX = {
    1: 0.00,
    2: 0.00,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}


@dataclass
class AHPResult:
    """Results returned by the AHP calculation."""

    weights: np.ndarray
    criteria: list[str]
    lambda_max: float
    consistency_index: float
    consistency_ratio: float
    is_consistent: bool


def validate_matrix(matrix: np.ndarray) -> np.ndarray:
    """Validate a positive reciprocal pairwise comparison matrix."""

    matrix = np.asarray(matrix, dtype=float)

    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("The comparison matrix must be square.")

    n = matrix.shape[0]

    if not 1 <= n <= 10:
        raise ValueError("Matrix size must be between 1 and 10.")

    if not np.all(np.isfinite(matrix)):
        raise ValueError("Matrix must contain only finite values.")

    if np.any(matrix <= 0):
        raise ValueError("All matrix values must be positive.")

    if not np.allclose(np.diag(matrix), 1.0):
        raise ValueError("All diagonal values must equal 1.")

    if not np.allclose(
        matrix * matrix.T,
        1.0,
        rtol=1e-7,
        atol=1e-7,
    ):
        raise ValueError(
            "Matrix must be reciprocal: a[j,i] = 1/a[i,j]."
        )

    return matrix


def calculate_ahp(
    matrix: np.ndarray,
    criteria: list[str] | None = None,
    threshold: float = 0.10,
) -> AHPResult:
    """Calculate AHP weights and consistency statistics.

    Parameters
    ----------
    matrix:
        Positive reciprocal pairwise comparison matrix.
    criteria:
        Optional names of the criteria.
    threshold:
        Maximum acceptable Consistency Ratio, between 0 and 1.

    Returns
    -------
    AHPResult
        Weights, lambda maximum, CI, CR and consistency status.

    Notes
    -----
    For matrices of size 1 or 2, CI and CR are defined as zero
    in this implementation.
    """

    matrix = validate_matrix(matrix)
    n = matrix.shape[0]

    # Validate consistency threshold
    if (
        not np.isscalar(threshold)
        or not np.isfinite(threshold)
        or not 0 <= threshold <= 1
    ):
        raise ValueError("Threshold must be between 0 and 1.")

    # Validate criterion names
    if criteria is None:
        criteria = [f"Criterion {i + 1}" for i in range(n)]
    else:
        if isinstance(criteria, str):
            raise ValueError("Criteria must be a list of names.")

        criteria = list(criteria)

        if len(criteria) != n:
            raise ValueError(
                "Number of criteria must match matrix dimensions."
            )

        if not all(
            isinstance(name, str) and name.strip()
            for name in criteria
        ):
            raise ValueError(
                "All criterion names must be non-empty strings."
            )

        criteria = [name.strip() for name in criteria]

        if len(set(criteria)) != n:
            raise ValueError("Criterion names must be unique.")

    # Principal right eigenvector
    eigenvalues, eigenvectors = np.linalg.eig(matrix)

    principal_index = int(np.argmax(eigenvalues.real))

    principal_eigenvalue = eigenvalues[principal_index]
    principal_eigenvector = eigenvectors[:, principal_index]

    # Check numerical stability
    if not np.isclose(principal_eigenvalue.imag, 0.0, atol=1e-8):
        raise ArithmeticError(
            "Principal eigenvalue is unexpectedly complex."
        )

    if not np.allclose(
        principal_eigenvector.imag,
        0.0,
        atol=1e-8,
    ):
        raise ArithmeticError(
            "Principal eigenvector is unexpectedly complex."
        )

    lambda_max = float(principal_eigenvalue.real)
    weights = principal_eigenvector.real

    # Normalize eigenvector sign
    if weights.sum() < 0:
        weights = -weights

    # A positive reciprocal matrix should have positive
    # principal eigenvector components.
    if np.any(weights <= 0):
        raise ArithmeticError(
            "Principal eigenvector contains non-positive values."
        )

    # Normalize weights
    weights = weights / weights.sum()

    if (
        not np.all(np.isfinite(weights))
        or not np.isclose(weights.sum(), 1.0)
    ):
        raise ArithmeticError("Invalid AHP weights calculated.")

    # Consistency Index and Consistency Ratio
    if n <= 2:
        consistency_index = 0.0
        consistency_ratio = 0.0
    else:
        consistency_index = max(
            0.0,
            (lambda_max - n) / (n - 1),
        )

        consistency_ratio = (
            consistency_index / RANDOM_INDEX[n]
        )

    return AHPResult(
        weights=weights,
        criteria=criteria,
        lambda_max=lambda_max,
        consistency_index=consistency_index,
        consistency_ratio=consistency_ratio,
        is_consistent=consistency_ratio <= threshold,
    )

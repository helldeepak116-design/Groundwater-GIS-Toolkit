
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

    if not np.allclose(matrix * matrix.T, 1.0, rtol=1e-7, atol=1e-7):
        raise ValueError("Matrix must be reciprocal: a[j,i] = 1/a[i,j].")

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
        Maximum acceptable Consistency Ratio.

    Returns
    -------
    AHPResult
        Weights, lambda maximum, CI, CR and consistency status.
    """

    matrix = validate_matrix(matrix)
    n = matrix.shape[0]

    if not np.isfinite(threshold) or threshold < 0:
        raise ValueError("Threshold must be a finite non-negative number.")

    if criteria is None:
        criteria = [f"Criterion {i + 1}" for i in range(n)]

    if len(criteria) != n:
        raise ValueError("Number of criteria must match matrix dimensions.")

    if len(set(criteria)) != n:
        raise ValueError("Criterion names must be unique.")

    # Principal right eigenvector
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    principal_index = int(np.argmax(eigenvalues.real))

    lambda_max = float(eigenvalues[principal_index].real)
    weights = eigenvectors[:, principal_index].real

    # Ensure positive normalized weights
    weights = np.abs(weights)
    weights = weights / weights.sum()

    # Consistency Index
    if n <= 2:
        consistency_index = 0.0
        consistency_ratio = 0.0
    else:
        consistency_index = max(0.0, (lambda_max - n) / (n - 1))
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

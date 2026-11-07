
import numpy as np
import pytest

from src.ahp import calculate_ahp, validate_matrix


def test_equal_comparison_weights():
    matrix = np.ones((3, 3))

    result = calculate_ahp(matrix)

    assert np.allclose(result.weights, [1/3, 1/3, 1/3])
    assert result.consistency_ratio == 0.0
    assert result.is_consistent


def test_known_pairwise_comparison():
    matrix = np.array([
        [1,   3,   5],
        [1/3, 1,   2],
        [1/5, 1/2, 1],
    ])

    result = calculate_ahp(
        matrix,
        criteria=["Geology", "Slope", "Rainfall"],
    )

    assert np.isclose(result.weights.sum(), 1.0)
    assert result.weights[0] > result.weights[1]
    assert result.weights[1] > result.weights[2]
    assert result.is_consistent


def test_invalid_non_square_matrix():
    with pytest.raises(ValueError):
        validate_matrix(np.array([[1, 2, 3], [2, 1, 2]]))


def test_invalid_reciprocal_matrix():
    matrix = np.array([
        [1, 3],
        [2, 1],
    ])

    with pytest.raises(ValueError):
        validate_matrix(matrix)


def test_criteria_length_mismatch():
    matrix = np.ones((3, 3))

    with pytest.raises(ValueError):
        calculate_ahp(matrix, criteria=["Geology", "Slope"])


def test_weights_are_normalized():
    matrix = np.array([
        [1, 2],
        [1/2, 1],
    ])

    result = calculate_ahp(matrix)

    assert np.isclose(result.weights.sum(), 1.0)

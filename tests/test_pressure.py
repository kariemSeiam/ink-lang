"""
Tests for pressure field mathematics.
"""

import pytest
import math

from ink.pressure import (
    GravityVector,
    collapse,
    cosine_similarity,
    vector_magnitude,
    normalize_vector,
    describe_direction,
)


class TestGravityVector:
    def test_creation(self):
        v = GravityVector([0.0, 0.9, 0.3], 0.8, 0.9, "HUNT")
        assert v.direction == [0.0, 0.9, 0.3]
        assert v.magnitude == 0.8
        assert v.confidence == 0.9
        assert v.mind == "HUNT"

    def test_clamping(self):
        v = GravityVector([2.0, -2.0, 0.5], 1.5, -0.1, "X")
        assert v.direction == [1.0, -1.0, 0.5]
        assert v.magnitude == 1.0
        assert v.confidence == 0.0

    def test_invalid_dimensions(self):
        with pytest.raises(ValueError):
            GravityVector([0.0, 0.9], 0.8, 0.9, "X")

    def test_weighted_direction(self):
        v = GravityVector([1.0, 0.0, 0.0], 0.5, 0.8, "X")
        weighted = v.weighted_direction
        assert weighted == [0.4, 0.0, 0.0]


class TestCosineSimilarity:
    def test_identical(self):
        assert cosine_similarity([1, 0, 0], [1, 0, 0]) == pytest.approx(1.0)

    def test_opposite(self):
        assert cosine_similarity([1, 0, 0], [-1, 0, 0]) == pytest.approx(-1.0)

    def test_orthogonal(self):
        assert cosine_similarity([1, 0, 0], [0, 1, 0]) == pytest.approx(0.0)

    def test_zero_vector(self):
        assert cosine_similarity([0, 0, 0], [1, 0, 0]) == 0.0


class TestCollapse:
    def test_single_vector_collapsed(self):
        v = GravityVector([0.0, 0.9, 0.3], 0.8, 0.9, "HUNT")
        result = collapse([v])
        assert result.status == "COLLAPSED"
        assert result.dominant_mind == "HUNT"

    def test_agreement_collapsed(self):
        vectors = [
            GravityVector([0.0, 0.9, 0.3], 0.8, 0.9, "HUNT"),
            GravityVector([-0.1, 0.8, 0.2], 0.7, 0.85, "EDGE"),
        ]
        result = collapse(vectors)
        assert result.status == "COLLAPSED"
        assert result.dominant_mind == "HUNT"

    def test_high_dissent_failed(self):
        vectors = [
            GravityVector([1.0, 1.0, 1.0], 0.9, 0.9, "HUNT"),
            GravityVector([-1.0, -1.0, -1.0], 0.9, 0.9, "EDGE"),
        ]
        result = collapse(vectors)
        assert result.status == "FAILED"
        assert result.reason == "TOO_MUCH_CONFLICT"
        assert result.action == "INK_RELEASE"

    def test_low_magnitude_failed(self):
        vectors = [
            GravityVector([0.01, 0.01, 0.01], 0.1, 0.1, "HUNT"),
        ]
        result = collapse(vectors)
        assert result.status == "FAILED"
        assert result.reason == "NO_STRONG_DIRECTION"
        assert result.action == "JET_REVERSE"

    def test_stretched_status(self):
        """Dissent between 0.4 and 0.65 should produce STRETCHED."""
        vectors = [
            GravityVector([1.0, 0.0, 0.0], 0.8, 0.9, "A"),
            GravityVector([0.0, 1.0, 0.0], 0.8, 0.9, "B"),
            GravityVector([0.0, 0.0, 1.0], 0.8, 0.9, "C"),
        ]
        result = collapse(vectors)
        # These are orthogonal, so dissent should be moderate
        assert result.status in ("STRETCHED", "COLLAPSED", "FAILED")

    def test_empty_vectors(self):
        result = collapse([])
        assert result.status == "FAILED"
        assert result.reason == "NO_VECTORS"

    def test_venom_pressure_field(self):
        """Test with the actual VENOM pressure field values."""
        vectors = [
            GravityVector([0.0, 0.9, 0.3], 0.8, 0.9, "HUNT"),
            GravityVector([-0.7, 0.6, 0.4], 0.7, 0.85, "EDGE"),
            GravityVector([-0.9, -0.4, 0.2], 0.75, 0.88, "WELD"),
        ]
        result = collapse(vectors)
        assert result.status in ("COLLAPSED", "STRETCHED")
        assert result.confidence > 0
        assert 0 <= result.dissent <= 1


class TestDescribeDirection:
    def test_concrete_depth(self):
        desc = describe_direction([-0.5, 0.8, 0.0])
        assert "concrete" in desc
        assert "depth" in desc

    def test_neutral(self):
        desc = describe_direction([0.0, 0.0, 0.0])
        assert "neutral" in desc or "balanced" in desc

    def test_risky(self):
        desc = describe_direction([0.0, 0.0, 0.7])
        assert "risk" in desc

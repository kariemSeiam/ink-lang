"""
Pressure field mathematics for INK.
Gravity vector algebra and collapse algorithm for multi-mind systems.

Axes (all normalized -1.0 to 1.0):
  X: concrete (-1.0) ←→ abstract (+1.0)
  Y: speed (-1.0) ←→ depth (+1.0)
  Z: safe (-1.0) ←→ risky (+1.0)

Units: All axes are dimensionless ratios. Angle calculations use cosine similarity.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class GravityVector:
    """
    A single mind's pull direction in the pressure field.
    """
    direction: list[float]  # [x, y, z] normalized -1.0 to 1.0
    magnitude: float        # strength of pull (0.0 - 1.0)
    confidence: float       # certainty of direction (0.0 - 1.0)
    mind: str               # which mind produced this

    def __post_init__(self):
        if len(self.direction) != 3:
            raise ValueError(f"Direction must be 3D vector, got {len(self.direction)} values")
        # Clamp values
        self.direction = [max(-1.0, min(1.0, v)) for v in self.direction]
        self.magnitude = max(0.0, min(1.0, self.magnitude))
        self.confidence = max(0.0, min(1.0, self.confidence))

    @property
    def weighted_direction(self) -> list[float]:
        """Direction weighted by magnitude * confidence."""
        weight = self.magnitude * self.confidence
        return [v * weight for v in self.direction]


@dataclass
class CollapseResult:
    """Result of collapsing a set of gravity vectors."""
    status: str              # COLLAPSED, STRETCHED, FAILED
    direction: list[float]   # resultant normalized direction
    confidence: float        # mean confidence across minds
    dissent: float           # mean cosine distance from resultant
    dominant_mind: str       # mind with strongest pull
    reason: str = ""         # reason for FAILED status
    action: str = ""         # recommended action for FAILED status
    raw_magnitude: float = 0.0  # magnitude before normalization


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def vector_magnitude(v: list[float]) -> float:
    """Compute magnitude of a vector."""
    return math.sqrt(sum(x * x for x in v))


def normalize_vector(v: list[float]) -> list[float]:
    """Normalize a vector to unit length."""
    mag = vector_magnitude(v)
    if mag == 0:
        return [0.0, 0.0, 0.0]
    return [x / mag for x in v]


def vector_sum(vectors: list[list[float]]) -> list[float]:
    """Sum multiple vectors element-wise."""
    if not vectors:
        return [0.0, 0.0, 0.0]
    result = [0.0, 0.0, 0.0]
    for v in vectors:
        for i in range(3):
            result[i] += v[i]
    return result


def collapse(
    vectors: list[GravityVector],
    dissent_threshold: float = 0.65,
    magnitude_threshold: float = 0.3,
) -> CollapseResult:
    """
    Collapse a set of gravity vectors into a single direction.

    Outcomes:
      - COLLAPSED: dissent < threshold, magnitude > threshold
      - STRETCHED: dissent between 0.4 and threshold
      - FAILED:TOO_MUCH_CONFLICT: dissent > threshold → INK_RELEASE
      - FAILED:NO_STRONG_DIRECTION: magnitude < threshold → JET_REVERSE
    """
    if not vectors:
        return CollapseResult(
            status="FAILED",
            direction=[0.0, 0.0, 0.0],
            confidence=0.0,
            dissent=0.0,
            dominant_mind="none",
            reason="NO_VECTORS",
            action="JET_REVERSE",
        )

    # Weight each vector by magnitude * confidence
    weighted = [v.weighted_direction for v in vectors]

    # Sum all weighted vectors
    resultant = vector_sum(weighted)
    raw_mag = vector_magnitude(resultant)

    # Normalize the resultant
    direction = normalize_vector(resultant)

    # Dissent: mean cosine distance from resultant
    if len(vectors) > 1:
        similarities = [
            cosine_similarity(direction, v.direction)
            for v in vectors
        ]
        dissent = 1.0 - (sum(similarities) / len(similarities))
    else:
        dissent = 0.0

    # Mean confidence
    confidence = sum(v.confidence for v in vectors) / len(vectors)

    # Dominant mind
    dominant = max(vectors, key=lambda v: v.magnitude * v.confidence)

    # Check thresholds
    if dissent > dissent_threshold:
        return CollapseResult(
            status="FAILED",
            direction=direction,
            confidence=confidence,
            dissent=dissent,
            dominant_mind=dominant.mind,
            reason="TOO_MUCH_CONFLICT",
            action="INK_RELEASE",
            raw_magnitude=raw_mag,
        )

    if raw_mag < magnitude_threshold:
        return CollapseResult(
            status="FAILED",
            direction=direction,
            confidence=confidence,
            dissent=dissent,
            dominant_mind=dominant.mind,
            reason="NO_STRONG_DIRECTION",
            action="JET_REVERSE",
            raw_magnitude=raw_mag,
        )

    # Determine COLLAPSED vs STRETCHED
    status = "COLLAPSED" if dissent < 0.4 else "STRETCHED"

    return CollapseResult(
        status=status,
        direction=direction,
        confidence=confidence,
        dissent=dissent,
        dominant_mind=dominant.mind,
        raw_magnitude=raw_mag,
    )


def describe_direction(direction: list[float]) -> str:
    """Convert a direction vector to a human-readable description."""
    x, y, z = direction

    parts = []

    # X axis: concrete ←→ abstract
    if abs(x) > 0.1:
        if x < 0:
            parts.append(f"concrete ({x:.2f})")
        else:
            parts.append(f"abstract ({x:+.2f})")

    # Y axis: speed ←→ depth
    if abs(y) > 0.1:
        if y > 0:
            parts.append(f"depth-seeking ({y:+.2f})")
        else:
            parts.append(f"speed-oriented ({y:+.2f})")

    # Z axis: safe ←→ risky
    if abs(z) > 0.1:
        if z > 0:
            parts.append(f"risk-taking ({z:+.2f})")
        else:
            parts.append(f"cautious ({z:+.2f})")

    if not parts:
        return "neutral / balanced"

    return " | ".join(parts)

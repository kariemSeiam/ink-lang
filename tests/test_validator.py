"""
Tests for the INK validator.
"""

import pytest
from pathlib import Path

from ink.parser import InkParser
from ink.validator import InkValidator, ValidationResult


EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
DISPOSITIONS_DIR = Path(__file__).parent.parent / "dispositions"


class TestValidator:
    def setup_method(self):
        self.parser = InkParser()
        self.validator = InkValidator()

    def _validate(self, source: str) -> ValidationResult:
        ast = self.parser.parse(source)
        return self.validator.validate(ast)

    def test_valid_basic(self):
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "walking on firm ground"
    COMPLETION_SIGNAL: "feet planted on solid ground"

  TRIGGER:input
    WHEN: msg.type == "query"
    ACTIVATES: @A::SENSATION::testing
    FALSE_POSITIVE_CHECK: msg.content.length > 0

  SATISFACTION:
    REQUIRES: confidence > 0.7
    HALT_ON_INCOMPLETE: true

  OVERRUN:
    DETECTION: iterations > 10
    CORRECTION: FORCE_COMPLETION("timeout")

  CRYSTALLIZATION:
    WARNING: same_pattern
    THRESHOLD: 3
    ACTION: SHELL_NULL
"""
        result = self._validate(source)
        assert result.valid, f"Errors: {[e.message for e in result.errors]}"

    def test_rule1_missing_feels_like(self):
        """Rule 1: FEELS_LIKE is required."""
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    COMPLETION_SIGNAL: "arrived"
"""
        result = self._validate(source)
        assert not result.valid
        assert any("missing FEELS_LIKE" in e.message for e in result.errors)

    def test_rule1_missing_completion_signal(self):
        """Rule 1: COMPLETION_SIGNAL is required."""
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "walking on ground"
"""
        result = self._validate(source)
        assert not result.valid
        assert any("missing COMPLETION_SIGNAL" in e.message for e in result.errors)

    def test_rule1_abstract_metaphor(self):
        """Rule 1: Abstract metaphors are rejected."""
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "uncertain"
    COMPLETION_SIGNAL: "hitting stone"
"""
        result = self._validate(source)
        assert not result.valid
        assert any("not a concrete sensory metaphor" in e.message for e in result.errors)

    def test_rule1_metric_as_metaphor(self):
        """Rule 1: Metrics are rejected as metaphors."""
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "confidence level 0.3"
    COMPLETION_SIGNAL: "hitting stone"
"""
        result = self._validate(source)
        assert not result.valid

    def test_rule2_missing_false_positive_check(self):
        """Rule 2: Every trigger must have FALSE_POSITIVE_CHECK."""
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "warm sun on face"
    COMPLETION_SIGNAL: "shadow passes"

  TRIGGER:input
    WHEN: msg.type == "query"
    ACTIVATES: @A::SENSATION::testing
"""
        result = self._validate(source)
        assert not result.valid
        assert any("FALSE_POSITIVE_CHECK" in e.message for e in result.errors)

    def test_rule3_missing_correction(self):
        """Rule 3: OVERRUN must have CORRECTION."""
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "warm sun on face"
    COMPLETION_SIGNAL: "shadow passes"

  OVERRUN:
    DETECTION: iterations > 10
"""
        result = self._validate(source)
        assert not result.valid
        assert any("missing CORRECTION" in e.message for e in result.errors)

    def test_rule3_invalid_correction_action(self):
        """Rule 3: CORRECTION must use a defined action."""
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "warm sun on face"
    COMPLETION_SIGNAL: "shadow passes"

  OVERRUN:
    DETECTION: iterations > 10
    CORRECTION: INVALID_ACTION("test")
"""
        result = self._validate(source)
        assert not result.valid
        assert any("unknown CORRECTION action" in e.message for e in result.errors)

    def test_rule4_invalid_crystallization_action(self):
        """Rule 4: CRYSTALLIZATION must use a defined action."""
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "warm sun on face"
    COMPLETION_SIGNAL: "shadow passes"

  CRYSTALLIZATION:
    WARNING: same pattern
    THRESHOLD: 3
    ACTION: INVALID_ACTION
"""
        result = self._validate(source)
        assert not result.valid
        assert any("unknown action" in e.message or "CRYSTALLIZATION" in e.message for e in result.errors)

    def test_rule5_missing_satisfaction_condition(self):
        """Rule 5: Every QUESTION must have SATISFACTION_CONDITION."""
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "warm sun on face"
    COMPLETION_SIGNAL: "shadow passes"

  QUESTION:is_done
    EVALUATES:
      - score
    OUTPUT: boolean
"""
        result = self._validate(source)
        assert not result.valid
        assert any("SATISFACTION_CONDITION" in e.message for e in result.errors)

    def test_rule6_invalid_reference(self):
        """Rule 6: References must be fully qualified."""
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "warm sun on face"
    COMPLETION_SIGNAL: "shadow passes"

  TRIGGER:input
    WHEN: msg.type == "query"
    ACTIVATES: @B::SENSATION::nonexistent
    FALSE_POSITIVE_CHECK: msg.content.length > 0
"""
        result = self._validate(source)
        assert not result.valid
        assert any("undefined mind" in e.message.lower() or "Undefined" in e.message for e in result.errors)

    def test_rule7_circular_dependency(self):
        """Rule 7: Mind cannot QUERY itself."""
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "warm sun on face"
    COMPLETION_SIGNAL: "shadow passes"

  INTERACTION:@A::@A
    RELATIONSHIP: lateral
    QUERIES: @A::SENSATION::testing
"""
        result = self._validate(source)
        assert not result.valid
        assert any("circular" in e.message.lower() for e in result.errors)

    def test_rule8_reserved_name(self):
        """Rule 8: Reserved names cannot be used."""
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:overrun
    FEELS_LIKE: "engine overheating"
    COMPLETION_SIGNAL: "temperature normal"
"""
        result = self._validate(source)
        assert not result.valid
        assert any("reserved" in e.message.lower() for e in result.errors)

    def test_rule11_pressure_field_undefined_mind(self):
        """Rule 11: Pressure field axes must reference defined minds."""
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "warm sun on face"
    COMPLETION_SIGNAL: "shadow passes"

@PRESSURE_FIELD
  @A AXIS: [0.0, 0.9, 0.3]
  @GHOST AXIS: [0.5, 0.5, 0.5]
  DISSENT_THRESHOLD: 0.65
  MAGNITUDE_THRESHOLD: 0.3
"""
        result = self._validate(source)
        assert not result.valid
        assert any("GHOST" in e.message for e in result.errors)

    def test_venom_example_valid(self):
        """The full VENOM example should pass validation."""
        ast = self.parser.parse_file(EXAMPLES_DIR / "venom.ink")
        result = self.validator.validate(ast)
        assert result.valid, f"Errors: {[e.message for e in result.errors]}"

    def test_all_dispositions_valid(self):
        """All built-in dispositions should pass validation."""
        for ink_file in DISPOSITIONS_DIR.glob("*.ink"):
            ast = self.parser.parse_file(ink_file)
            result = self.validator.validate(ast)
            assert result.valid, f"{ink_file.name} failed: {[e.message for e in result.errors]}"

    def test_concrete_metaphor_accepted(self):
        """Good sensory metaphors should pass."""
        good_metaphors = [
            "standing on ice that might crack",
            "word on tip of tongue",
            "door closing flush",
            "splinter under fingernail",
            "bridge with a gap",
            "metal under hammer",
            "warm sun on face",
            "running fingers through sand",
        ]
        for metaphor in good_metaphors:
            source = f"""---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "{metaphor}"
    COMPLETION_SIGNAL: "hitting stone"
"""
            result = self._validate(source)
            assert result.valid, f"Good metaphor rejected: {metaphor}"

    def test_abstract_metaphor_rejected(self):
        """Abstract words should fail validation."""
        bad_metaphors = [
            "uncertain",
            "not optimal",
        ]
        for metaphor in bad_metaphors:
            source = f"""---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "{metaphor}"
    COMPLETION_SIGNAL: "hitting stone"
"""
            result = self._validate(source)
            assert not result.valid, f"Bad metaphor accepted: {metaphor}"

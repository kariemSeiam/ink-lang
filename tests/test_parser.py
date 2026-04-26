"""
Tests for the INK parser.
"""

import pytest
from pathlib import Path

from ink.parser import InkParser
from ink.errors import ParseError, IndentMismatch


EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
DISPOSITIONS_DIR = Path(__file__).parent.parent / "dispositions"

BASIC_INK = """---
VERSION: 1.0.0
SYSTEM: TestSystem
MINDS: [ALPHA]
---

@MIND:ALPHA

  SENSATION:testing
    FEELS_LIKE: "walking on firm ground"
    COMPLETION_SIGNAL: "arrived at destination"

  TRIGGER:input_received
    WHEN: message.type == "query"
    ACTIVATES: @ALPHA::SENSATION::testing
    FALSE_POSITIVE_CHECK: message.content.length > 0

  SATISFACTION:
    REQUIRES: confidence > 0.7
    HALT_ON_INCOMPLETE: true

  OVERRUN:
    DETECTION: iterations > 10
    CORRECTION: FORCE_COMPLETION("timeout")

  CRYSTALLIZATION:
    WARNING: same_pattern_repeated
    THRESHOLD: 3
    ACTION: SHELL_NULL
"""


class TestParser:
    def setup_method(self):
        self.parser = InkParser()

    def test_parse_basic(self):
        ast = self.parser.parse(BASIC_INK)
        assert ast.header.version == "1.0.0"
        assert ast.header.system == "TestSystem"
        assert "ALPHA" in ast.minds

    def test_parse_sensation(self):
        ast = self.parser.parse(BASIC_INK)
        alpha = ast.minds["ALPHA"]
        assert "testing" in alpha.sensations
        s = alpha.sensations["testing"]
        assert s.feels_like == "walking on firm ground"
        assert s.completion_signal == "arrived at destination"

    def test_parse_trigger(self):
        ast = self.parser.parse(BASIC_INK)
        alpha = ast.minds["ALPHA"]
        assert "input_received" in alpha.triggers
        t = alpha.triggers["input_received"]
        assert t.when == 'message.type == "query"'
        assert t.activates == "@ALPHA::SENSATION::testing"
        assert t.false_positive_check == "message.content.length > 0"

    def test_parse_satisfaction(self):
        ast = self.parser.parse(BASIC_INK)
        alpha = ast.minds["ALPHA"]
        assert alpha.satisfaction is not None
        assert "confidence > 0.7" in alpha.satisfaction.requires
        assert alpha.satisfaction.halt_on_incomplete is True

    def test_parse_overrun(self):
        ast = self.parser.parse(BASIC_INK)
        alpha = ast.minds["ALPHA"]
        assert alpha.overrun is not None
        assert alpha.overrun.detection == "iterations > 10"
        assert alpha.overrun.correction_action == "FORCE_COMPLETION"
        assert alpha.overrun.correction_reason == "timeout"

    def test_parse_crystallization(self):
        ast = self.parser.parse(BASIC_INK)
        alpha = ast.minds["ALPHA"]
        assert alpha.crystallization is not None
        assert alpha.crystallization.warning == "same_pattern_repeated"
        assert alpha.crystallization.threshold == 3
        assert alpha.crystallization.action == "SHELL_NULL"

    def test_parse_state(self):
        source = """---
VERSION: 1.0.0
SYSTEM: TestSystem
MINDS: [BETA]
---

@MIND:BETA

  SENSATION:testing
    FEELS_LIKE: "warm sun on face"
    COMPLETION_SIGNAL: "shadow passes — moment captured"

  STATE:depth_level
    DEFAULT: 0
    -> 1 WHEN sources_count >= 1
    -> 2 WHEN sources_count >= 3
    -> 3 WHEN sources_count >= 5 AND cross_validated == true
"""
        ast = self.parser.parse(source)
        beta = ast.minds["BETA"]
        assert "depth_level" in beta.states
        st = beta.states["depth_level"]
        assert st.default == "0"
        assert len(st.transitions) == 3
        assert st.transitions[0].target == 1
        assert st.transitions[0].condition == "sources_count >= 1"

    def test_parse_question(self):
        source = """---
VERSION: 1.0.0
SYSTEM: TestSystem
MINDS: [GAMMA]
---

@MIND:GAMMA

  SENSATION:testing
    FEELS_LIKE: "holding a tuning fork"
    COMPLETION_SIGNAL: "the note is pure"

  QUESTION:is_done
    EVALUATES:
      - score
      - coverage
    OUTPUT: boolean
    SATISFACTION_CONDITION: score >= 3
"""
        ast = self.parser.parse(source)
        gamma = ast.minds["GAMMA"]
        assert "is_done" in gamma.questions
        q = gamma.questions["is_done"]
        assert "score" in q.evaluates
        assert "coverage" in q.evaluates
        assert q.output_type == "boolean"
        assert q.satisfaction_condition == "score >= 3"

    def test_parse_interaction(self):
        source = """---
VERSION: 1.0.0
SYSTEM: TestSystem
MINDS: [ALPHA, BETA]
---

@MIND:ALPHA

  SENSATION:testing
    FEELS_LIKE: "warm stone under hand"
    COMPLETION_SIGNAL: "heat spreads evenly"

  INTERACTION:@ALPHA::@BETA
    RELATIONSHIP: lateral
    QUERIES: @BETA::SENSATION::testing

@MIND:BETA

  SENSATION:testing
    FEELS_LIKE: "cool water on wrists"
    COMPLETION_SIGNAL: "refreshed"
"""
        ast = self.parser.parse(source)
        alpha = ast.minds["ALPHA"]
        assert len(alpha.interactions) == 1
        inter = alpha.interactions[0]
        assert inter.target_mind == "BETA"
        assert inter.relationship == "lateral"
        assert inter.queries == "@BETA::SENSATION::testing"

    def test_parse_pressure_field(self):
        source = """---
VERSION: 1.0.0
SYSTEM: TestSystem
MINDS: [A, B]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "wind in hair"
    COMPLETION_SIGNAL: "stillness"

@MIND:B

  SENSATION:testing
    FEELS_LIKE: "feet in stream"
    COMPLETION_SIGNAL: "dry ground"

@PRESSURE_FIELD
  @A AXIS: [0.0, 0.9, 0.3]
  @B AXIS: [-0.7, 0.6, 0.4]
  RESOLUTION: vector_sum
  DISSENT_THRESHOLD: 0.65
  MAGNITUDE_THRESHOLD: 0.3
"""
        ast = self.parser.parse(source)
        assert ast.pressure_field is not None
        assert len(ast.pressure_field.axes) == 2
        assert ast.pressure_field.axes[0].mind_name == "A"
        assert ast.pressure_field.axes[0].vector == [0.0, 0.9, 0.3]
        assert ast.pressure_field.dissent_threshold == 0.65

    def test_parse_collapse(self):
        source = """---
VERSION: 1.0.0
SYSTEM: TestSystem
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "light through prism"
    COMPLETION_SIGNAL: "spectrum clear"

@COLLAPSE
  METHOD: vector_sum
  THRESHOLD: 0.65

  OUTPUT:
    FORMAT: natural_language
    INCLUDE: [answer, confidence, dissent_level]

  - CONDITION: dissent > 0.65
    ACTION: INK_RELEASE
  - CONDITION: magnitude < 0.3
    ACTION: JET_REVERSE
"""
        ast = self.parser.parse(source)
        assert ast.collapse is not None
        assert ast.collapse.method == "vector_sum"
        assert ast.collapse.output_format == "natural_language"
        assert "answer" in ast.collapse.output_includes
        assert len(ast.collapse.fallbacks) == 2
        assert ast.collapse.fallbacks[0].condition == "dissent > 0.65"
        assert ast.collapse.fallbacks[0].action == "INK_RELEASE"

    def test_tabs_raise_error(self):
        source = "---\nVERSION: 1.0.0\n---\n@MIND:A\n\tSENSATION:x\n\t\tFEELS_LIKE: \"y\""
        with pytest.raises(IndentMismatch):
            self.parser.parse(source)

    def test_parse_venom_example(self):
        """Parse the full VENOM example file."""
        ast = self.parser.parse_file(EXAMPLES_DIR / "venom.ink")
        assert ast.header.system == "VENOM"
        assert set(ast.minds.keys()) == {"HUNT", "EDGE", "WELD"}
        assert ast.pressure_field is not None
        assert ast.collapse is not None
        assert len(ast.pressure_field.axes) == 3

    def test_parse_all_dispositions(self):
        """All built-in dispositions parse without error."""
        for ink_file in DISPOSITIONS_DIR.glob("*.ink"):
            ast = self.parser.parse_file(ink_file)
            assert ast.minds, f"No minds in {ink_file.name}"

    def test_multiple_sensations(self):
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [M]
---

@MIND:M

  SENSATION:first
    FEELS_LIKE: "morning dew on grass"
    COMPLETION_SIGNAL: "sun dries the last drop"

  SENSATION:second
    FEELS_LIKE: "fire in hearth"
    COMPLETION_SIGNAL: "embers settle to ash"
"""
        ast = self.parser.parse(source)
        m = ast.minds["M"]
        assert len(m.sensations) == 2
        assert "first" in m.sensations
        assert "second" in m.sensations

    def test_mind_list_parsing(self):
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [ALPHA, BETA, GAMMA]
---

@MIND:ALPHA

  SENSATION:test
    FEELS_LIKE: "stone in hand"
    COMPLETION_SIGNAL: "stone placed"
"""
        ast = self.parser.parse(source)
        assert ast.header.minds == ["ALPHA", "BETA", "GAMMA"]

"""
Tests for the visualizer.
"""

import pytest
from pathlib import Path

from ink.parser import InkParser
from ink.visualizer import InkVisualizer


EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


class TestVisualizer:
    def setup_method(self):
        self.parser = InkParser()
        self.visualizer = InkVisualizer()
        self.ast = self.parser.parse_file(EXAMPLES_DIR / "venom.ink")

    def test_mind_graph(self):
        result = self.visualizer.mind_graph(self.ast)
        assert "graph TD" in result
        assert "HUNT" in result
        assert "EDGE" in result
        assert "WELD" in result

    def test_interaction_diagram(self):
        result = self.visualizer.interaction_diagram(self.ast)
        assert "sequenceDiagram" in result
        assert "HUNT" in result
        assert "EDGE" in result

    def test_pressure_field_diagram(self):
        result = self.visualizer.pressure_field_diagram(self.ast)
        assert "graph LR" in result
        assert "HUNT" in result
        assert "Pressure Field" in result

    def test_no_pressure_field(self):
        """File without pressure field should return a message."""
        source = """---
VERSION: 1.0.0
SYSTEM: Test
MINDS: [A]
---

@MIND:A

  SENSATION:testing
    FEELS_LIKE: "stone in hand"
    COMPLETION_SIGNAL: "stone placed"
"""
        ast = self.parser.parse(source)
        result = self.visualizer.pressure_field_diagram(ast)
        assert "No pressure field" in result

    def test_graph_has_sensation_nodes(self):
        result = self.visualizer.mind_graph(self.ast)
        assert "standing on ice" in result
        assert "splinter" in result
        assert "bridge" in result

    def test_graph_has_interactions(self):
        result = self.visualizer.mind_graph(self.ast)
        assert "lateral" in result

    def test_graph_has_overrun(self):
        result = self.visualizer.mind_graph(self.ast)
        assert "Overrun" in result

    def test_graph_has_crystallization(self):
        result = self.visualizer.mind_graph(self.ast)
        assert "Crystallize" in result or "crystallize" in result.lower()

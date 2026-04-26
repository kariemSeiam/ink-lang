"""
Tests for the INK compiler.
"""

import pytest
import json
from pathlib import Path

from ink.parser import InkParser
from ink.compiler import InkCompiler
from ink.errors import UnsupportedTarget


EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


class TestCompiler:
    def setup_method(self):
        self.parser = InkParser()
        self.compiler = InkCompiler()
        self.ast = self.parser.parse_file(EXAMPLES_DIR / "venom.ink")

    def test_generic_target(self):
        result = self.compiler.compile(self.ast, target="generic")
        assert "HUNT" in result
        assert "EDGE" in result
        assert "WELD" in result
        assert "standing on ice" in result
        assert "splinter under fingernail" in result
        assert "bridge with a gap" in result

    def test_openai_target(self):
        result = self.compiler.compile(self.ast, target="openai")
        assert "multi-mind" in result.lower() or "mind" in result.lower()
        assert "standing on ice" in result
        assert "Satisfied only when" in result or "satisfied" in result.lower()

    def test_anthropic_target(self):
        result = self.compiler.compile(self.ast, target="anthropic")
        assert "<mind" in result
        assert "<sensation" in result
        assert "<feels_like>" in result
        assert "standing on ice" in result
        assert "</mind>" in result

    def test_json_target(self):
        result = self.compiler.compile(self.ast, target="json")
        data = json.loads(result)
        assert "minds" in data
        assert "HUNT" in data["minds"]
        assert "EDGE" in data["minds"]
        assert "WELD" in data["minds"]

        hunt = data["minds"]["HUNT"]
        assert "shallow_knowledge" in hunt["sensations"]
        assert hunt["sensations"]["shallow_knowledge"]["feels_like"] == "standing on ice that might crack"

    def test_json_includes_pressure_field(self):
        result = self.compiler.compile(self.ast, target="json")
        data = json.loads(result)
        assert "pressure_field" in data
        assert "HUNT" in data["pressure_field"]["axes"]

    def test_single_mind_compile(self):
        result = self.compiler.compile(self.ast, target="generic", mind_name="HUNT")
        assert "HUNT" in result
        assert "EDGE" not in result

    def test_unsupported_target(self):
        with pytest.raises(UnsupportedTarget):
            self.compiler.compile(self.ast, target="nonexistent")

    def test_anthropic_xml_well_formed(self):
        """Anthropic output should have matching XML tags."""
        result = self.compiler.compile(self.ast, target="anthropic")
        assert result.count("<mind") == result.count("</mind>")
        assert result.count("<sensation") == result.count("</sensation>")

    def test_generic_has_pressure_field(self):
        result = self.compiler.compile(self.ast, target="generic")
        assert "Pressure Field" in result
        assert "concrete" in result

    def test_generic_has_collapse(self):
        result = self.compiler.compile(self.ast, target="generic")
        assert "Collapse" in result
        assert "INK_RELEASE" in result

    def test_openai_has_overrun(self):
        result = self.compiler.compile(self.ast, target="openai")
        assert "overrun" in result.lower()
        assert "FORCE_COMPLETION" in result

    def test_compile_disposition_file(self):
        """Test compiling a single-mind disposition."""
        dispositions_dir = Path(__file__).parent.parent / "dispositions"
        ast = self.parser.parse_file(dispositions_dir / "hunt.ink")
        result = self.compiler.compile(ast, target="generic")
        assert "HUNT" in result
        assert "running fingers through sand" in result

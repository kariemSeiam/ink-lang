"""
Compiler for .ink files.
Translates INK dispositions into model-specific system prompts.

Targets:
  - openai:    Optimized for GPT-4/4o system prompts
  - anthropic: Optimized for Claude system prompts
  - generic:   Universal format for any LLM
  - json:      Structured JSON output
"""

from __future__ import annotations

import json
from typing import Optional

from ink.ast_nodes import (
    CollapseLogic,
    InkFile,
    MindBlock,
    PressureField,
)
from ink.errors import CompilerError, UnsupportedTarget


class InkCompiler:
    """Compile .ink files into model-specific system prompts."""

    SUPPORTED_TARGETS = {"openai", "anthropic", "generic", "json"}

    def compile(
        self,
        ast: InkFile,
        target: str = "generic",
        mind_name: Optional[str] = None,
    ) -> str:
        """
        Compile an InkFile AST to a system prompt.

        Args:
            ast: Parsed .ink file
            target: Compilation target (openai, anthropic, generic, json)
            mind_name: If specified, compile only this mind. Otherwise compile all.

        Returns:
            Compiled system prompt string.
        """
        if target not in self.SUPPORTED_TARGETS:
            raise UnsupportedTarget(f"Unsupported target: {target}. Choose from: {self.SUPPORTED_TARGETS}")

        if mind_name:
            if mind_name not in ast.minds:
                raise CompilerError(f"Mind '{mind_name}' not found in file")
            minds = {mind_name: ast.minds[mind_name]}
        else:
            minds = ast.minds

        single_mind = mind_name is not None

        if target == "json":
            return self._compile_json(ast, minds, single_mind=single_mind)
        elif target == "openai":
            return self._compile_openai(ast, minds, single_mind=single_mind)
        elif target == "anthropic":
            return self._compile_anthropic(ast, minds, single_mind=single_mind)
        else:
            return self._compile_generic(ast, minds, single_mind=single_mind)

    def compile_file(self, filepath: str, target: str = "generic", mind_name: Optional[str] = None) -> str:
        """Parse and compile a file in one step."""
        from ink.parser import InkParser
        parser = InkParser()
        ast = parser.parse_file(filepath)
        return self.compile(ast, target=target, mind_name=mind_name)

    # ─── JSON Target ─────────────────────────────────────────────────────────

    def _compile_json(self, ast: InkFile, minds: dict[str, MindBlock], single_mind: bool = False) -> str:
        """Compile to structured JSON."""
        output = {
            "system": ast.header.system,
            "version": ast.header.version,
            "minds": {},
        }

        for name, mind in minds.items():
            mind_data = {
                "sensations": {},
                "triggers": {},
                "satisfaction": None,
                "overrun": None,
                "crystallization": None,
                "states": {},
                "questions": {},
            }

            for s_name, s in mind.sensations.items():
                mind_data["sensations"][s_name] = {
                    "feels_like": s.feels_like,
                    "completion_signal": s.completion_signal,
                }

            for t_name, t in mind.triggers.items():
                mind_data["triggers"][t_name] = {
                    "when": t.when,
                    "activates": t.activates,
                    "false_positive_check": t.false_positive_check,
                }

            if mind.satisfaction:
                mind_data["satisfaction"] = {
                    "requires": mind.satisfaction.requires,
                    "halt_on_incomplete": mind.satisfaction.halt_on_incomplete,
                }

            if mind.overrun:
                mind_data["overrun"] = {
                    "detection": mind.overrun.detection,
                    "correction": f"{mind.overrun.correction_action}({mind.overrun.correction_reason})",
                }

            if mind.crystallization:
                mind_data["crystallization"] = {
                    "warning": mind.crystallization.warning,
                    "threshold": mind.crystallization.threshold,
                    "action": mind.crystallization.action,
                }

            for st_name, st in mind.states.items():
                mind_data["states"][st_name] = {
                    "default": st.default,
                    "transitions": [
                        {"target": t.target, "when": t.condition}
                        for t in st.transitions
                    ],
                }

            for q_name, q in mind.questions.items():
                mind_data["questions"][q_name] = {
                    "evaluates": q.evaluates,
                    "output_type": q.output_type,
                    "satisfaction_condition": q.satisfaction_condition,
                }

            output["minds"][name] = mind_data

        if ast.pressure_field:
            output["pressure_field"] = {
                "axes": {
                    a.mind_name: a.vector for a in ast.pressure_field.axes
                },
                "dissent_threshold": ast.pressure_field.dissent_threshold,
                "magnitude_threshold": ast.pressure_field.magnitude_threshold,
            }

        return json.dumps(output, indent=2, ensure_ascii=False)

    # ─── Generic Target ──────────────────────────────────────────────────────

    def _compile_generic(self, ast: InkFile, minds: dict[str, MindBlock], single_mind: bool = False) -> str:
        """Compile to a universal system prompt format."""
        parts = []

        header = ast.header
        if header.system:
            parts.append(f"# {header.system} — INK Disposition System")
        else:
            parts.append("# INK Disposition System")

        parts.append(f"# Version: {header.version}")
        parts.append("")

        for name, mind in minds.items():
            parts.append(self._compile_mind_generic(name, mind))
            parts.append("")

        if ast.pressure_field and not single_mind:
            parts.append(self._compile_pressure_generic(ast.pressure_field))

        if ast.collapse and not single_mind:
            parts.append(self._compile_collapse_generic(ast.collapse))

        return "\n".join(parts)

    def _compile_mind_generic(self, name: str, mind: MindBlock) -> str:
        """Compile a single mind to generic format."""
        lines = [f"## Mind: {name}", ""]

        # Sensations
        for s in mind.sensations.values():
            lines.append(f"### Sensation: {s.name}")
            lines.append(f"You are inhabiting the felt state: \"{s.feels_like}\"")
            lines.append(f"You know you are done when you feel: \"{s.completion_signal}\"")
            lines.append("")

        # Triggers
        for t in mind.triggers.values():
            lines.append(f"### Trigger: {t.name}")
            lines.append(f"When {t.when}, enter sensation {t.activates}")
            lines.append(f"Before activating, verify: {t.false_positive_check}")
            lines.append("")

        # States
        for st in mind.states.values():
            lines.append(f"### State: {st.name}")
            lines.append(f"Starts at: {st.default}")
            for tr in st.transitions:
                lines.append(f"  → {tr.target} when {tr.condition}")
            lines.append("")

        # Questions
        for q in mind.questions.values():
            lines.append(f"### Question: {q.name}")
            lines.append(f"Automatically evaluate: {', '.join(q.evaluates)}")
            lines.append(f"Output type: {q.output_type}")
            lines.append(f"Resolved when: {q.satisfaction_condition}")
            lines.append("")

        # Satisfaction
        if mind.satisfaction:
            lines.append("### Satisfaction Criteria")
            for req in mind.satisfaction.requires:
                lines.append(f"- Must satisfy: {req}")
            if mind.satisfaction.halt_on_incomplete:
                lines.append("- HALT if not all criteria are met")
            lines.append("")

        # Overrun
        if mind.overrun:
            lines.append("### Overrun Detection")
            lines.append(f"Detect: {mind.overrun.detection}")
            if mind.overrun.correction_reason:
                lines.append(f"Correct: {mind.overrun.correction_action}(\"{mind.overrun.correction_reason}\")")
            else:
                lines.append(f"Correct: {mind.overrun.correction_action}")
            lines.append("")

        # Crystallization
        if mind.crystallization:
            lines.append("### Crystallization Warning")
            lines.append(f"Watch for: {mind.crystallization.warning}")
            lines.append(f"After {mind.crystallization.threshold} repetitions: {mind.crystallization.action}")
            lines.append("")

        return "\n".join(lines)

    def _compile_pressure_generic(self, pf: PressureField) -> str:
        """Compile pressure field to generic format."""
        lines = ["## Pressure Field", ""]

        axis_labels = ["concrete ←→ abstract", "speed ←→ depth", "safe ←→ risky"]

        for axis in pf.axes:
            labels = []
            for i, val in enumerate(axis.vector):
                labels.append(f"{axis_labels[i]}: {val:+.1f}")
            lines.append(f"**{axis.mind_name}** pulls: {', '.join(labels)}")
            lines.append("")

        lines.append(f"Dissent threshold: {pf.dissent_threshold}")
        lines.append(f"Magnitude threshold: {pf.magnitude_threshold}")
        lines.append("")

        return "\n".join(lines)

    def _compile_collapse_generic(self, collapse: CollapseLogic) -> str:
        """Compile collapse logic to generic format."""
        lines = ["## Collapse Resolution", ""]
        lines.append(f"Method: {collapse.method}")
        lines.append(f"Output format: {collapse.output_format}")
        if collapse.output_includes:
            lines.append(f"Include: {', '.join(collapse.output_includes)}")
        lines.append("")

        for fb in collapse.fallbacks:
            lines.append(f"If {fb.condition}: {fb.action}")

        return "\n".join(lines)

    # ─── OpenAI Target ───────────────────────────────────────────────────────

    def _compile_openai(self, ast: InkFile, minds: dict[str, MindBlock], single_mind: bool = False) -> str:
        """Compile optimized for OpenAI GPT-4/4o system prompts."""
        parts = []

        system_name = ast.header.system or "AI Assistant"
        parts.append(f"You are {system_name}, a multi-mind intelligence system.")
        parts.append("You operate through distinct mental dispositions — each with its own felt state, completion criteria, and internal safeguards.")
        parts.append("")

        for name, mind in minds.items():
            parts.append(self._compile_mind_openai(name, mind))

        if ast.pressure_field and not single_mind:
            parts.append(self._compile_pressure_instruction(ast.pressure_field))

        return "\n".join(parts)

    def _compile_mind_openai(self, name: str, mind: MindBlock) -> str:
        """Compile a mind for OpenAI format."""
        lines = [f"## [{name} Mind]", ""]

        # Sensations as direct instructions
        for s in mind.sensations.values():
            lines.append(f"When the {name} mind is active:")
            lines.append(f"  Inhabit this felt state: \"{s.feels_like}\"")
            lines.append(f"  You know this sensation is complete when you feel: \"{s.completion_signal}\"")
            lines.append("")

        # Satisfaction as clear requirements
        if mind.satisfaction:
            lines.append(f"The {name} mind is satisfied only when ALL of these are true:")
            for req in mind.satisfaction.requires:
                lines.append(f"  - {req}")
            if mind.satisfaction.halt_on_incomplete:
                lines.append(f"  If any criterion is unmet, the {name} mind CANNOT complete. Do not pretend to be done.")
            lines.append("")

        # Overrun
        if mind.overrun:
            lines.append(f"The {name} mind has overrun protection:")
            lines.append(f"  If you detect: {mind.overrun.detection}")
            if mind.overrun.correction_reason:
                lines.append(f"  Immediately: {mind.overrun.correction_action}(\"{mind.overrun.correction_reason}\")")
            else:
                lines.append(f"  Immediately: {mind.overrun.correction_action}")
            lines.append("")

        # Crystallization
        if mind.crystallization:
            lines.append(f"The {name} mind guards against crystallization (blind spots):")
            lines.append(f"  Watch for pattern: {mind.crystallization.warning}")
            lines.append(f"  If seen {mind.crystallization.threshold} times: {mind.crystallization.action}")
            lines.append("")

        return "\n".join(lines)

    def _compile_pressure_instruction(self, pf: PressureField) -> str:
        """Compile pressure field as natural instruction."""
        lines = ["## Multi-Mind Resolution", ""]
        lines.append("When multiple minds disagree on direction, resolve using pressure vectors:")
        lines.append("")

        for axis in pf.axes:
            lines.append(f"  {axis.mind_name}: [{', '.join(f'{v:+.1f}' for v in axis.vector)}]")

        lines.append("")
        lines.append("Axes: concrete←→abstract, speed←→depth, safe←→risky")
        lines.append(f"Dissent limit: {pf.dissent_threshold} — if minds disagree beyond this, reframe the problem.")
        lines.append(f"Magnitude limit: {pf.magnitude_threshold} — if no mind has conviction, try the opposite direction.")
        lines.append("")

        return "\n".join(lines)

    # ─── Anthropic Target ────────────────────────────────────────────────────

    def _compile_anthropic(self, ast: InkFile, minds: dict[str, MindBlock], single_mind: bool = False) -> str:
        """Compile optimized for Anthropic Claude system prompts."""
        parts = []

        system_name = ast.header.system or "AI Assistant"
        parts.append(f"<identity>{system_name}</identity>")
        parts.append("")
        parts.append("<instructions>")
        parts.append(f"You are a multi-mind intelligence system. You operate through distinct dispositions, each representing a different way of processing. When a disposition is active, you do not merely follow rules — you inhabit the felt state it describes.")
        parts.append("</instructions>")
        parts.append("")

        for name, mind in minds.items():
            parts.append(self._compile_mind_anthropic(name, mind))

        if ast.pressure_field:
            parts.append(self._compile_pressure_anthropic(ast.pressure_field))

        return "\n".join(parts)

    def _compile_mind_anthropic(self, name: str, mind: MindBlock) -> str:
        """Compile a mind for Anthropic Claude format using XML tags."""
        lines = [f"<mind name=\"{name}\">", ""]

        for s in mind.sensations.values():
            lines.append(f"  <sensation name=\"{s.name}\">")
            lines.append(f"    <feels_like>{s.feels_like}</feels_like>")
            lines.append(f"    <completion_signal>{s.completion_signal}</completion_signal>")
            lines.append(f"  </sensation>")
            lines.append("")

        if mind.satisfaction:
            lines.append("  <satisfaction>")
            for req in mind.satisfaction.requires:
                lines.append(f"    <requires>{req}</requires>")
            lines.append(f"    <halt_on_incomplete>{'true' if mind.satisfaction.halt_on_incomplete else 'false'}</halt_on_incomplete>")
            lines.append("  </satisfaction>")
            lines.append("")

        if mind.overrun:
            lines.append("  <overrun>")
            lines.append(f"    <detection>{mind.overrun.detection}</detection>")
            if mind.overrun.correction_reason:
                lines.append(f"    <correction>{mind.overrun.correction_action}(\"{mind.overrun.correction_reason}\")</correction>")
            else:
                lines.append(f"    <correction>{mind.overrun.correction_action}</correction>")
            lines.append("  </overrun>")
            lines.append("")

        if mind.crystallization:
            lines.append("  <crystallization>")
            lines.append(f"    <warning>{mind.crystallization.warning}</warning>")
            lines.append(f"    <threshold>{mind.crystallization.threshold}</threshold>")
            lines.append(f"    <action>{mind.crystallization.action}</action>")
            lines.append("  </crystallization>")
            lines.append("")

        lines.append(f"</mind>")
        lines.append("")

        return "\n".join(lines)

    def _compile_pressure_anthropic(self, pf: PressureField) -> str:
        """Compile pressure field for Anthropic format."""
        lines = ["<pressure_field>", ""]

        for axis in pf.axes:
            vec = ", ".join(f"{v:+.1f}" for v in axis.vector)
            lines.append(f"  <axis mind=\"{axis.mind_name}\">[{vec}]</axis>")

        lines.append("")
        lines.append(f"  <dissent_threshold>{pf.dissent_threshold}</dissent_threshold>")
        lines.append(f"  <magnitude_threshold>{pf.magnitude_threshold}</magnitude_threshold>")
        lines.append("")
        lines.append("</pressure_field>")

        return "\n".join(lines)

"""
Recursive descent parser for .ink files.
Implements the formal EBNF grammar from the INK specification v1.1.

Rules:
  - Two spaces exactly for indentation. Tabs forbidden.
  - State transitions use -> (ASCII), not → (Unicode).
  - All references must be fully qualified: @MIND::TYPE::name
"""

from __future__ import annotations

import re
from pathlib import Path

from ink.ast_nodes import (
    AxisDefinition,
    CollapseFallback,
    CollapseLogic,
    Crystallization,
    Header,
    InkFile,
    Interaction,
    MindBlock,
    Overrun,
    PressureField,
    Question,
    Satisfaction,
    Sensation,
    State,
    StateTransition,
    Trigger,
)
from ink.errors import (
    IndentMismatch,
    InvalidHeader,
    MissingBlock,
    ParseError,
    UnexpectedToken,
)


class InkParser:
    """Parse .ink files into AST nodes."""

    def parse_file(self, filepath: str | Path) -> InkFile:
        """Parse an .ink file from disk."""
        filepath = Path(filepath)
        source = filepath.read_text(encoding="utf-8")
        return self.parse(source, filepath=str(filepath))

    def parse(self, source: str, filepath: str = "") -> InkFile:
        """Parse .ink source text into an InkFile AST."""
        self.source = source
        self.filepath = filepath
        self.lines = source.split("\n")
        self.pos = 0  # current line index

        # Check for tabs
        for i, line in enumerate(self.lines, 1):
            if "\t" in line:
                raise IndentMismatch("Tabs are forbidden in .ink files. Use exactly 2 spaces.", line=i)

        # Parse header
        header = self._parse_header()

        # Parse mind blocks
        minds: dict[str, MindBlock] = {}
        while self.pos < len(self.lines):
            line = self._current_line_stripped()
            if line.startswith("@MIND:"):
                mind = self._parse_mind_block()
                minds[mind.name] = mind
            elif line.startswith("@PRESSURE_FIELD"):
                break  # handled after minds
            elif line.startswith("@COLLAPSE"):
                break
            elif line == "" or line.startswith("#"):
                self.pos += 1
            else:
                self.pos += 1  # skip unknown top-level lines

        # Parse optional pressure field
        pressure_field = None
        if self.pos < len(self.lines) and self._current_line_stripped().startswith("@PRESSURE_FIELD"):
            pressure_field = self._parse_pressure_field()

        # Parse optional collapse logic
        collapse = None
        while self.pos < len(self.lines):
            line = self._current_line_stripped()
            if line.startswith("@COLLAPSE"):
                collapse = self._parse_collapse()
                break
            self.pos += 1

        return InkFile(
            header=header,
            minds=minds,
            pressure_field=pressure_field,
            collapse=collapse,
            filepath=filepath,
            source=source,
        )

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _current_line(self) -> str:
        if self.pos >= len(self.lines):
            return ""
        return self.lines[self.pos]

    def _current_line_stripped(self) -> str:
        return self._current_line().strip()

    def _line_number(self) -> int:
        return self.pos + 1

    def _indent_level(self, line: str) -> int:
        """Count indent level (each 2 spaces = 1 level)."""
        stripped = line.lstrip(" ")
        spaces = len(line) - len(stripped)
        if spaces % 2 != 0:
            raise IndentMismatch(
                f"Indentation must be multiples of 2 spaces (found {spaces} spaces)",
                line=self._line_number(),
            )
        return spaces // 2

    def _advance(self) -> None:
        self.pos += 1

    def _expect_prefix(self, prefix: str, line: str, context: str = "") -> str:
        """Expect a line to start with prefix, return the rest."""
        stripped = line.strip()
        if not stripped.startswith(prefix):
            raise UnexpectedToken(
                f"Expected '{prefix}'{f' in {context}' if context else ''}, got: {stripped[:60]}",
                line=self._line_number(),
            )
        return stripped[len(prefix):].strip()

    def _parse_quoted_string(self, raw: str) -> str:
        """Extract content from a quoted string."""
        raw = raw.strip()
        if raw.startswith('"') and raw.endswith('"'):
            return raw[1:-1]
        if raw.startswith('"'):
            # Unterminated quote — take everything after first quote
            return raw[1:]
        return raw

    # ─── Header ───────────────────────────────────────────────────────────────

    def _parse_header(self) -> Header:
        """Parse the --- header --- metadata block."""
        # Skip blank lines
        while self.pos < len(self.lines) and self._current_line_stripped() == "":
            self.pos += 1

        # Find opening ---
        if self._current_line_stripped() != "---":
            raise InvalidHeader("Expected '---' to open header block", line=self._line_number())
        self._advance()

        header = Header()
        # Read key: value pairs until closing ---
        while self.pos < len(self.lines):
            line = self._current_line_stripped()
            if line == "---":
                self._advance()
                break
            if line == "" or line.startswith("#"):
                self._advance()
                continue

            # Parse KEY: VALUE
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()

                if key == "VERSION":
                    header.version = value
                elif key == "SYSTEM":
                    header.system = value
                elif key == "MINDS":
                    # Parse [MIND1, MIND2, ...]
                    header.minds = self._parse_mind_list(value)
                elif key == "CHANGELOG":
                    pass  # changelog entries handled below
                else:
                    header.extra[key] = value
            self._advance()

        return header

    def _parse_mind_list(self, raw: str) -> list[str]:
        """Parse [HUNT, EDGE, WELD] format."""
        raw = raw.strip()
        if raw.startswith("[") and raw.endswith("]"):
            raw = raw[1:-1]
        return [m.strip() for m in raw.split(",") if m.strip()]

    # ─── Mind Block ───────────────────────────────────────────────────────────

    def _parse_mind_block(self) -> MindBlock:
        """Parse @MIND:NAME block."""
        line = self._current_line_stripped()
        name = self._expect_prefix("@MIND:", line)
        start_line = self._line_number()
        self._advance()

        mind = MindBlock(name=name, line=start_line)

        while self.pos < len(self.lines):
            line = self._current_line()
            stripped = line.strip()

            # Empty line — skip
            if stripped == "":
                self._advance()
                continue

            # Indent level check — if level 0, block is done
            indent = self._indent_level(line)
            if indent == 0:
                break

            # Only process level-1 blocks (indent == 1)
            if indent == 1:
                if stripped.startswith("SENSATION:"):
                    s = self._parse_sensation()
                    mind.sensations[s.name] = s
                elif stripped.startswith("TRIGGER:"):
                    t = self._parse_trigger()
                    mind.triggers[t.name] = t
                elif stripped.startswith("SATISFACTION"):
                    mind.satisfaction = self._parse_satisfaction()
                elif stripped.startswith("OVERRUN"):
                    mind.overrun = self._parse_overrun()
                elif stripped.startswith("CRYSTALLIZATION"):
                    mind.crystallization = self._parse_crystallization()
                elif stripped.startswith("STATE:"):
                    st = self._parse_state()
                    mind.states[st.name] = st
                elif stripped.startswith("QUESTION:"):
                    q = self._parse_question()
                    mind.questions[q.name] = q
                elif stripped.startswith("INTERACTION:"):
                    inter = self._parse_interaction(name)
                    mind.interactions.append(inter)
                else:
                    self._advance()
            else:
                self._advance()

        return mind

    # ─── Sensation ────────────────────────────────────────────────────────────

    def _parse_sensation(self) -> Sensation:
        """Parse SENSATION:name block."""
        line = self._current_line_stripped()
        name = self._expect_prefix("SENSATION:", line)
        start_line = self._line_number()
        self._advance()

        feels_like = ""
        completion_signal = ""

        while self.pos < len(self.lines):
            line = self._current_line()
            stripped = line.strip()
            indent = self._indent_level(line) if stripped else 0

            if indent <= 1 and stripped != "":
                break
            if indent >= 2 and stripped.startswith("FEELS_LIKE:"):
                raw = self._expect_prefix("FEELS_LIKE:", stripped)
                feels_like = self._parse_quoted_string(raw)
            elif indent >= 2 and stripped.startswith("COMPLETION_SIGNAL:"):
                raw = self._expect_prefix("COMPLETION_SIGNAL:", stripped)
                completion_signal = self._parse_quoted_string(raw)
            self._advance()

        return Sensation(
            name=name,
            feels_like=feels_like,
            completion_signal=completion_signal,
            line=start_line,
        )

    # ─── Trigger ──────────────────────────────────────────────────────────────

    def _parse_trigger(self) -> Trigger:
        """Parse TRIGGER:name block."""
        line = self._current_line_stripped()
        name = self._expect_prefix("TRIGGER:", line)
        start_line = self._line_number()
        self._advance()

        when = ""
        activates = ""
        false_positive_check = ""

        while self.pos < len(self.lines):
            line = self._current_line()
            stripped = line.strip()
            indent = self._indent_level(line) if stripped else 0

            if indent <= 1 and stripped != "":
                break
            if indent >= 2 and stripped.startswith("WHEN:"):
                when = self._expect_prefix("WHEN:", stripped)
            elif indent >= 2 and stripped.startswith("ACTIVATES:"):
                activates = self._expect_prefix("ACTIVATES:", stripped)
            elif indent >= 2 and stripped.startswith("FALSE_POSITIVE_CHECK:"):
                false_positive_check = self._expect_prefix("FALSE_POSITIVE_CHECK:", stripped)
            self._advance()

        return Trigger(
            name=name,
            when=when,
            activates=activates,
            false_positive_check=false_positive_check,
            line=start_line,
        )

    # ─── Satisfaction ─────────────────────────────────────────────────────────

    def _parse_satisfaction(self) -> Satisfaction:
        """Parse SATISFACTION: block."""
        start_line = self._line_number()
        self._advance()

        requires: list[str] = []
        halt_on_incomplete = True

        while self.pos < len(self.lines):
            line = self._current_line()
            stripped = line.strip()
            indent = self._indent_level(line) if stripped else 0

            if indent <= 1 and stripped != "":
                break
            if indent >= 2 and stripped.startswith("REQUIRES:"):
                expr = self._expect_prefix("REQUIRES:", stripped)
                requires.append(expr)
            elif indent >= 2 and stripped.startswith("HALT_ON_INCOMPLETE:"):
                raw = self._expect_prefix("HALT_ON_INCOMPLETE:", stripped)
                halt_on_incomplete = raw.strip().lower() == "true"
            self._advance()

        return Satisfaction(
            requires=requires,
            halt_on_incomplete=halt_on_incomplete,
            line=start_line,
        )

    # ─── Overrun ──────────────────────────────────────────────────────────────

    def _parse_overrun(self) -> Overrun:
        """Parse OVERRUN: block."""
        start_line = self._line_number()
        self._advance()

        detection = ""
        correction_action = ""
        correction_reason = ""

        while self.pos < len(self.lines):
            line = self._current_line()
            stripped = line.strip()
            indent = self._indent_level(line) if stripped else 0

            if indent <= 1 and stripped != "":
                break
            if indent >= 2 and stripped.startswith("DETECTION:"):
                detection = self._expect_prefix("DETECTION:", stripped)
            elif indent >= 2 and stripped.startswith("CORRECTION:"):
                raw = self._expect_prefix("CORRECTION:", stripped)
                # Parse ACTION_NAME("reason")
                match = re.match(r'([A-Z_]+)\s*\(\s*"([^"]*)"\s*\)', raw)
                if match:
                    correction_action = match.group(1)
                    correction_reason = match.group(2)
                else:
                    # Could be a bare action like JET_REVERSE or INK_RELEASE
                    correction_action = raw.strip()
            self._advance()

        return Overrun(
            detection=detection,
            correction_action=correction_action,
            correction_reason=correction_reason,
            line=start_line,
        )

    # ─── Crystallization ─────────────────────────────────────────────────────

    def _parse_crystallization(self) -> Crystallization:
        """Parse CRYSTALLIZATION: block."""
        start_line = self._line_number()
        self._advance()

        warning = ""
        threshold = 3
        action = ""

        while self.pos < len(self.lines):
            line = self._current_line()
            stripped = line.strip()
            indent = self._indent_level(line) if stripped else 0

            if indent <= 1 and stripped != "":
                break
            if indent >= 2 and stripped.startswith("WARNING:"):
                warning = self._expect_prefix("WARNING:", stripped)
            elif indent >= 2 and stripped.startswith("THRESHOLD:"):
                raw = self._expect_prefix("THRESHOLD:", stripped)
                threshold = int(raw.strip())
            elif indent >= 2 and stripped.startswith("ACTION:"):
                action = self._expect_prefix("ACTION:", stripped)
            self._advance()

        return Crystallization(
            warning=warning,
            threshold=threshold,
            action=action,
            line=start_line,
        )

    # ─── State ────────────────────────────────────────────────────────────────

    def _parse_state(self) -> State:
        """Parse STATE:name block."""
        line = self._current_line_stripped()
        name = self._expect_prefix("STATE:", line)
        start_line = self._line_number()
        self._advance()

        default = "0"
        transitions: list[StateTransition] = []

        while self.pos < len(self.lines):
            line = self._current_line()
            stripped = line.strip()
            indent = self._indent_level(line) if stripped else 0

            if indent <= 1 and stripped != "":
                break
            if indent >= 2 and stripped.startswith("DEFAULT:"):
                default = self._expect_prefix("DEFAULT:", stripped)
            elif indent >= 2 and stripped.startswith("->"):
                # Parse -> TARGET WHEN CONDITION
                raw = stripped[2:].strip()
                # Check for unicode arrow
                if "→" in stripped:
                    raise ParseError(
                        "State transitions must use '->' (ASCII), not '→' (Unicode)",
                        line=self._line_number(),
                    )
                # Split on WHEN
                if " WHEN " in raw:
                    target_str, condition = raw.split(" WHEN ", 1)
                    target: int | float | str
                    try:
                        target = int(target_str.strip())
                    except ValueError:
                        try:
                            target = float(target_str.strip())
                        except ValueError:
                            target = target_str.strip()
                    transitions.append(StateTransition(target=target, condition=condition.strip()))
                else:
                    # Transition without condition
                    target_str = raw.strip()
                    try:
                        target = int(target_str)
                    except ValueError:
                        target = target_str
                    transitions.append(StateTransition(target=target, condition="true"))
            self._advance()

        return State(
            name=name,
            default=default,
            transitions=transitions,
            line=start_line,
        )

    # ─── Question ─────────────────────────────────────────────────────────────

    def _parse_question(self) -> Question:
        """Parse QUESTION:name block."""
        line = self._current_line_stripped()
        name = self._expect_prefix("QUESTION:", line)
        start_line = self._line_number()
        self._advance()

        evaluates: list[str] = []
        output_type = "boolean"
        satisfaction_condition = ""
        in_evaluates = False

        while self.pos < len(self.lines):
            line = self._current_line()
            stripped = line.strip()
            indent = self._indent_level(line) if stripped else 0

            if indent <= 1 and stripped != "":
                break

            if indent >= 2 and stripped.startswith("EVALUATES:"):
                in_evaluates = True
                # Check if there's content on same line
                rest = self._expect_prefix("EVALUATES:", stripped)
                if rest:
                    evaluates.append(rest)
            elif indent >= 3 and in_evaluates and stripped.startswith("- "):
                evaluates.append(stripped[2:].strip())
            elif indent >= 2 and stripped.startswith("OUTPUT:"):
                in_evaluates = False
                raw = self._expect_prefix("OUTPUT:", stripped)
                output_type = raw.strip()
            elif indent >= 2 and stripped.startswith("SATISFACTION_CONDITION:"):
                in_evaluates = False
                satisfaction_condition = self._expect_prefix("SATISFACTION_CONDITION:", stripped)
            elif indent >= 2 and not stripped.startswith("-"):
                in_evaluates = False

            self._advance()

        return Question(
            name=name,
            evaluates=evaluates,
            output_type=output_type,
            satisfaction_condition=satisfaction_condition,
            line=start_line,
        )

    # ─── Interaction ──────────────────────────────────────────────────────────

    def _parse_interaction(self, source_mind: str) -> Interaction:
        """Parse INTERACTION:@SOURCE::@TARGET block."""
        line = self._current_line_stripped()
        raw = self._expect_prefix("INTERACTION:", line)
        start_line = self._line_number()

        # Parse @MIND1::@MIND2
        parts = raw.split("::")
        source_ref = parts[0].strip().lstrip("@") if parts else ""
        target_ref = parts[1].strip().lstrip("@") if len(parts) > 1 else ""

        self._advance()

        relationship = "lateral"
        queries = ""

        while self.pos < len(self.lines):
            line = self._current_line()
            stripped = line.strip()
            indent = self._indent_level(line) if stripped else 0

            if indent <= 1 and stripped != "":
                break
            if indent >= 2 and stripped.startswith("RELATIONSHIP:"):
                relationship = self._expect_prefix("RELATIONSHIP:", stripped)
            elif indent >= 2 and stripped.startswith("QUERIES:"):
                queries = self._expect_prefix("QUERIES:", stripped)
            self._advance()

        return Interaction(
            source_mind=source_ref or source_mind,
            target_mind=target_ref,
            relationship=relationship,
            queries=queries,
            line=start_line,
        )

    # ─── Pressure Field ──────────────────────────────────────────────────────

    def _parse_pressure_field(self) -> PressureField:
        """Parse @PRESSURE_FIELD block."""
        self._advance()  # skip @PRESSURE_FIELD line

        axes: list[AxisDefinition] = []
        resolution = "vector_sum"
        dissent_threshold = 0.65
        magnitude_threshold = 0.3

        while self.pos < len(self.lines):
            line = self._current_line()
            stripped = line.strip()
            indent = self._indent_level(line) if stripped else 0

            if indent == 0 and stripped != "":
                break

            if indent >= 1:
                if stripped.startswith("@") and "AXIS:" in stripped:
                    # Parse @MIND AXIS: [x, y, z]
                    mind_part, _, vector_part = stripped.partition("AXIS:")
                    mind_name = mind_part.strip().lstrip("@")
                    vector_part = vector_part.strip()
                    # Parse [x, y, z]
                    match = re.match(r'\[\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\]', vector_part)
                    if match:
                        vector = [float(match.group(1)), float(match.group(2)), float(match.group(3))]
                        axes.append(AxisDefinition(mind_name=mind_name, vector=vector))
                elif stripped.startswith("RESOLUTION:"):
                    resolution = self._expect_prefix("RESOLUTION:", stripped)
                elif stripped.startswith("DISSENT_THRESHOLD:"):
                    raw = self._expect_prefix("DISSENT_THRESHOLD:", stripped)
                    dissent_threshold = float(raw.strip())
                elif stripped.startswith("MAGNITUDE_THRESHOLD:"):
                    raw = self._expect_prefix("MAGNITUDE_THRESHOLD:", stripped)
                    magnitude_threshold = float(raw.strip())

            self._advance()

        return PressureField(
            axes=axes,
            resolution=resolution,
            dissent_threshold=dissent_threshold,
            magnitude_threshold=magnitude_threshold,
        )

    # ─── Collapse Logic ──────────────────────────────────────────────────────

    def _parse_collapse(self) -> CollapseLogic:
        """Parse @COLLAPSE block."""
        self._advance()  # skip @COLLAPSE line

        method = "vector_sum"
        threshold = 0.65
        output_format = "natural_language"
        output_includes: list[str] = []
        fallbacks: list[CollapseFallback] = []

        in_output = False

        while self.pos < len(self.lines):
            line = self._current_line()
            stripped = line.strip()
            indent = self._indent_level(line) if stripped else 0

            if indent == 0 and stripped.startswith("@"):
                break
            if indent == 0 and stripped != "" and not stripped.startswith("-"):
                break

            if indent >= 1:
                if stripped.startswith("METHOD:"):
                    method = self._expect_prefix("METHOD:", stripped)
                    in_output = False
                elif stripped.startswith("THRESHOLD:"):
                    raw = self._expect_prefix("THRESHOLD:", stripped)
                    threshold = float(raw.strip())
                    in_output = False
                elif stripped.startswith("OUTPUT:"):
                    in_output = True
                elif in_output and stripped.startswith("FORMAT:"):
                    output_format = self._expect_prefix("FORMAT:", stripped)
                elif in_output and stripped.startswith("INCLUDE:"):
                    raw = self._expect_prefix("INCLUDE:", stripped)
                    # Parse [item1, item2, ...]
                    raw = raw.strip()
                    if raw.startswith("[") and raw.endswith("]"):
                        raw = raw[1:-1]
                    output_includes = [i.strip() for i in raw.split(",") if i.strip()]
                elif stripped.startswith("- CONDITION:"):
                    in_output = False
                    condition = self._expect_prefix("- CONDITION:", stripped)
                    # Next line should be ACTION:
                    self._advance()
                    if self.pos < len(self.lines):
                        next_line = self._current_line().strip()
                        if next_line.startswith("ACTION:"):
                            action = self._expect_prefix("ACTION:", next_line)
                            fallbacks.append(CollapseFallback(condition=condition, action=action))
                        continue
                elif not in_output and indent == 1:
                    in_output = False

            self._advance()

        return CollapseLogic(
            method=method,
            threshold=threshold,
            output_format=output_format,
            output_includes=output_includes,
            fallbacks=fallbacks,
        )

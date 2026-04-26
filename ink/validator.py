"""
Validator for .ink files.
Implements all 11 validation rules from the INK specification v1.1.

Rules:
 1. Every FEELS_LIKE uses concrete sensory metaphor
 2. Every TRIGGER has FALSE_POSITIVE_CHECK
 3. Every OVERRUN has CORRECTION using a defined action
 4. Every CRYSTALLIZATION has ACTION using a defined action
 5. Every QUESTION has SATISFACTION_CONDITION
 6. All references are fully qualified and resolve to defined items
 7. No circular dependencies (mind cannot QUERY itself)
 8. No reserved names used as user-defined names
 9. Indentation is exactly two spaces (checked in parser)
10. State transitions use -> not → (checked in parser)
11. INTERACTION cross-mind queries reference existing minds
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ink.ast_nodes import InkFile, MindBlock
from ink.errors import (
    RESERVED_NAMES,
    VALID_CORRECTION_ACTIONS,
    VALID_CRYSTALLIZATION_ACTIONS,
    CircularDependency,
    InvalidAction,
    InvalidBlockType,
    InvalidMetaphor,
    MissingRequired,
    ReservedName,
    UndefinedItem,
    UndefinedMind,
    ValidationError,
)


@dataclass
class ValidationIssue:
    """A single validation issue."""
    rule: int
    message: str
    line: int | None = None
    severity: str = "error"  # error, warning


@dataclass
class ValidationResult:
    """Result of validating an .ink file."""
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def add_error(self, rule: int, message: str, line: int | None = None) -> None:
        self.issues.append(ValidationIssue(rule=rule, message=message, line=line, severity="error"))
        self.valid = False

    def add_warning(self, rule: int, message: str, line: int | None = None) -> None:
        self.issues.append(ValidationIssue(rule=rule, message=message, line=line, severity="warning"))


class InkValidator:
    """Validate parsed .ink files against all specification rules."""

    def validate(self, ast: InkFile) -> ValidationResult:
        """Validate a parsed InkFile AST."""
        result = ValidationResult(valid=True)

        # Check header
        if not ast.header:
            result.add_error(0, "Missing header block")
            return result

        if not ast.minds:
            result.add_error(0, "No @MIND blocks defined")
            return result

        # Validate each mind
        for mind in ast.minds.values():
            self._validate_mind(mind, result)

        # Cross-mind validation
        self._validate_references(ast, result)
        self._validate_interactions(ast, result)

        # Pressure field validation
        if ast.pressure_field:
            self._validate_pressure_field(ast, result)

        return result

    def validate_file(self, filepath: str) -> ValidationResult:
        """Parse and validate a file in one step."""
        from ink.parser import InkParser
        parser = InkParser()
        ast = parser.parse_file(filepath)
        return self.validate(ast)

    # ─── Mind Validation ─────────────────────────────────────────────────────

    def _validate_mind(self, mind: MindBlock, result: ValidationResult) -> None:
        """Validate a single mind block."""
        mind_label = f"@MIND:{mind.name}"

        # Must have at least one SENSATION
        if not mind.sensations:
            result.add_error(1, f"{mind_label} has no SENSATION blocks", line=mind.line)
            return

        # Validate each sensation
        for s in mind.sensations.values():
            self._validate_sensation(s, mind_label, result)

        # Rule 2: Every TRIGGER has FALSE_POSITIVE_CHECK
        for t in mind.triggers.values():
            if not t.false_positive_check:
                result.add_error(
                    2,
                    f"{mind_label} TRIGGER:{t.name} missing FALSE_POSITIVE_CHECK",
                    line=t.line,
                )

        # Rule 3: Every OVERRUN has CORRECTION using a defined action
        if mind.overrun:
            if not mind.overrun.correction_action:
                result.add_error(
                    3,
                    f"{mind_label} OVERRUN missing CORRECTION",
                    line=mind.overrun.line,
                )
            elif mind.overrun.correction_action not in VALID_CORRECTION_ACTIONS:
                result.add_error(
                    3,
                    f"{mind_label} OVERRUN unknown CORRECTION action: {mind.overrun.correction_action}",
                    line=mind.overrun.line,
                )

        # Rule 4: Every CRYSTALLIZATION has ACTION using a defined action
        if mind.crystallization:
            if not mind.crystallization.action:
                result.add_error(
                    4,
                    f"{mind_label} CRYSTALLIZATION missing ACTION",
                    line=mind.crystallization.line,
                )
            elif mind.crystallization.action not in VALID_CRYSTALLIZATION_ACTIONS:
                result.add_error(
                    4,
                    f"{mind_label} CRYSTALLIZATION unknown action: {mind.crystallization.action}",
                    line=mind.crystallization.line,
                )

        # Rule 5: Every QUESTION has SATISFACTION_CONDITION
        for q in mind.questions.values():
            if not q.satisfaction_condition:
                result.add_error(
                    5,
                    f"{mind_label} QUESTION:{q.name} missing SATISFACTION_CONDITION",
                    line=q.line,
                )

        # Rule 8: No reserved names
        for s_name in mind.sensations:
            if s_name in RESERVED_NAMES:
                result.add_error(
                    8,
                    f"{mind_label} SENSATION:{s_name} uses reserved name",
                    line=mind.sensations[s_name].line,
                )
        for st_name in mind.states:
            if st_name in RESERVED_NAMES:
                result.add_error(
                    8,
                    f"{mind_label} STATE:{st_name} uses reserved name",
                    line=mind.states[st_name].line,
                )

    # ─── Sensation Validation ────────────────────────────────────────────────

    def _validate_sensation(self, sensation, mind_label: str, result: ValidationResult) -> None:
        """Validate a single sensation block."""
        label = f"{mind_label} SENSATION:{sensation.name}"

        # FEELS_LIKE is required
        if not sensation.feels_like:
            result.add_error(1, f"{label} missing FEELS_LIKE", line=sensation.line)
        else:
            # Rule 1: Must be concrete sensory metaphor
            if not self._is_concrete_metaphor(sensation.feels_like):
                result.add_error(
                    1,
                    f"{label} FEELS_LIKE is not a concrete sensory metaphor: \"{sensation.feels_like}\"",
                    line=sensation.line,
                )

        # COMPLETION_SIGNAL is required
        if not sensation.completion_signal:
            result.add_error(
                1,
                f"{label} missing COMPLETION_SIGNAL",
                line=sensation.line,
            )
        else:
            if not self._is_concrete_metaphor(sensation.completion_signal):
                result.add_error(
                    1,
                    f"{label} COMPLETION_SIGNAL is not a concrete sensory metaphor: \"{sensation.completion_signal}\"",
                    line=sensation.line,
                )

    @staticmethod
    def _is_concrete_metaphor(text: str) -> bool:
        """
        Heuristic check: a concrete sensory metaphor should NOT be:
        - A single abstract word (uncertain, good, bad, ready, done)
        - A metric or number (confidence > 0.5, level 3)
        - Pure optimization language (optimal, efficient, ready)

        It SHOULD contain sensory language: touch, temperature, texture,
        movement, weight, sound, visual imagery.
        """
        text = text.strip().lower()

        # Reject pure metrics / numeric expressions
        if re.match(r'^[\d\s><=!().+\-*/a-z_]+$', text):
            # Contains no sensory words at all → likely a metric
            sensory_words = [
                "like", "feels", "as if", "touch", "stone", "ice",
                "water", "weight", "solid", "soft", "hard", "warm",
                "cold", "light", "dark", "sound", "silence",
                "smooth", "rough", "bridge", "door", "floor",
                "sand", "finger", "fingernail", "surface", "fire",
                "wind", "rain", "sun", "moon", "earth", "metal",
                "wood", "glass", "air", "breath", "heart", "bone",
                "blood", "sweat", "tear", "ground", "sky", "sea",
                "ocean", "mountain", "river", "rock", "cloud",
                "ember", "flame", "spark", "dust", "mud", "fog",
                "mist", "shadow", "echo", "thunder", "lightning",
                "hammer", "anvil", "forge", "needle", "thread",
                "fabric", "silk", "velvet", "iron", "steel",
                "rope", "chain", "wire", "string", "tuning",
                "tongue", "lip", "teeth", "eye", "ear", "skin",
                "palm", "wrist", "shoulder", "back", "step",
                "walk", "run", "stand", "sit", "fall", "rise",
                "push", "pull", "hold", "release", "catch", "drop",
                "crack", "break", "tear", "rip", "snap", "click",
                "ring", "hum", "buzz", "vibrate", "shake", "pulse",
                "glow", "shine", "flash", "burn", "freeze", "melt",
                "sink", "float", "dive", "climb", "reach", "grab",
                "close", "open", "shut", "slam", "lock", "seal",
                "dew", "frost", "heat", "warmth", "chill", "shiver",
                "taste", "smell", "sight", "hearing", "touch",
                "wet", "dry", "damp", "crisp", "sharp", "blunt",
                "edge", "point", "tip", "curve", "bend", "fold",
                "splash", "ripple", "wave", "tide", "current",
                "corridor", "room", "hall", "wall", "ceiling",
                "prism", "spectrum", "lens", "mirror", "glass",
                "hearth", "ash", "ember", "coal", "soot",
                "orchestra", "note", "rhythm", "tempo", "beat",
                "conductor", "symphony", "chord", "melody",
                "scabbard", "blade", "sword", "shield", "armor",
                "tinder", "flint", "steel", "match", "candle",
                "lantern", "torch", "lamp", "beacon", "lighthouse",
            ]
            if not any(w in text for w in sensory_words):
                return False

        # Reject single abstract words
        abstract_words = {
            "uncertain", "certain", "confident", "ready", "done", "complete",
            "incomplete", "good", "bad", "optimal", "not optimal", "satisfied",
            "unsatisfied", "prepared", "unprepared",
        }
        if text.strip().rstrip(".") in abstract_words:
            return False

        # Reject pure metric patterns like "confidence level 0.3"
        if re.match(r'^confidence\s+(level\s+)?[\d.<>=]+', text):
            return False

        return True

    # ─── Reference Validation ────────────────────────────────────────────────

    def _validate_references(self, ast: InkFile, result: ValidationResult) -> None:
        """Rule 6: All references must be fully qualified and resolve."""
        for mind in ast.minds.values():
            for ref in mind.get_all_references():
                self._resolve_reference(ref, ast, result, mind.name)

    def _resolve_reference(
        self, ref: str, ast: InkFile, result: ValidationResult, source_mind: str
    ) -> None:
        """Resolve a fully qualified reference."""
        parts = ref.split("::")

        if len(parts) != 3:
            result.add_error(
                6,
                f"Invalid reference format: '{ref}'. Expected @MIND::TYPE::name",
            )
            return

        mind_name = parts[0].lstrip("@")
        block_type = parts[1]
        item_name = parts[2]

        # Check mind exists
        if mind_name not in ast.minds:
            result.add_error(6, f"Reference to undefined mind: '@{mind_name}' in {ref}")
            return

        # Check block type
        if block_type not in ("SENSATION", "STATE", "QUESTION"):
            result.add_error(6, f"Invalid block type '{block_type}' in reference: {ref}")
            return

        # Check item exists
        target_mind = ast.minds[mind_name]
        if block_type == "SENSATION" and item_name not in target_mind.sensations:
            result.add_error(6, f"Undefined item: {ref}")
        elif block_type == "STATE" and item_name not in target_mind.states:
            result.add_error(6, f"Undefined item: {ref}")
        elif block_type == "QUESTION" and item_name not in target_mind.questions:
            result.add_error(6, f"Undefined item: {ref}")

    # ─── Interaction Validation ──────────────────────────────────────────────

    def _validate_interactions(self, ast: InkFile, result: ValidationResult) -> None:
        """Rules 7 & 11: Circular deps and cross-mind reference validation."""
        for mind in ast.minds.values():
            for interaction in mind.interactions:
                # Rule 7: No self-reference
                if interaction.source_mind == interaction.target_mind:
                    result.add_error(
                        7,
                        f"@MIND:{mind.name} cannot QUERY itself (circular dependency)",
                        line=interaction.line,
                    )

                # Rule 11: Target mind must exist
                if interaction.target_mind not in ast.minds:
                    result.add_error(
                        11,
                        f"@MIND:{mind.name} INTERACTION references undefined mind: @{interaction.target_mind}",
                        line=interaction.line,
                    )

    # ─── Pressure Field Validation ───────────────────────────────────────────

    def _validate_pressure_field(self, ast: InkFile, result: ValidationResult) -> None:
        """Validate pressure field references and thresholds."""
        pf = ast.pressure_field

        for axis in pf.axes:
            if axis.mind_name not in ast.minds:
                result.add_error(
                    11,
                    f"@PRESSURE_FIELD references undefined mind: @{axis.mind_name}",
                )

            if len(axis.vector) != 3:
                result.add_error(
                    11,
                    f"Axis for @{axis.mind_name} must have exactly 3 values, got {len(axis.vector)}",
                )

        if not (0.0 <= pf.dissent_threshold <= 1.0):
            result.add_error(
                11,
                f"DISSENT_THRESHOLD must be between 0.0 and 1.0, got {pf.dissent_threshold}",
            )

        if not (0.0 <= pf.magnitude_threshold <= 1.0):
            result.add_error(
                11,
                f"MAGNITUDE_THRESHOLD must be between 0.0 and 1.0, got {pf.magnitude_threshold}",
            )

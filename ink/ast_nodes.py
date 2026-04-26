"""
AST node definitions for INK language.
Every construct from the formal grammar is represented as a dataclass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ─── Header ───────────────────────────────────────────────────────────────────

@dataclass
class Header:
    """The metadata header block between --- delimiters."""
    version: str = ""
    system: str = ""
    minds: list[str] = field(default_factory=list)
    changelog: dict[str, str] = field(default_factory=dict)
    extra: dict[str, str] = field(default_factory=dict)


# ─── Sensation ────────────────────────────────────────────────────────────────

@dataclass
class Sensation:
    """The felt state a mind inhabits. Not behavior. Not output. The internal experience."""
    name: str
    feels_like: str = ""          # concrete sensory metaphor (required)
    completion_signal: str = ""   # felt experience of being done (required)
    line: int = 0


# ─── Trigger ──────────────────────────────────────────────────────────────────

@dataclass
class Trigger:
    """What causes a sensation to activate."""
    name: str
    when: str = ""                           # condition expression
    activates: str = ""                       # fully qualified @MIND::SENSATION::name ref
    false_positive_check: str = ""            # required on every trigger
    line: int = 0


# ─── Satisfaction ─────────────────────────────────────────────────────────────

@dataclass
class Satisfaction:
    """External validation criteria. Computational. Measurable."""
    requires: list[str] = field(default_factory=list)  # boolean expressions
    halt_on_incomplete: bool = True
    line: int = 0


# ─── Overrun ──────────────────────────────────────────────────────────────────

@dataclass
class Overrun:
    """Internal self-detection when a sensation persists past usefulness."""
    detection: str = ""                      # condition expression
    correction_action: str = ""              # e.g. FORCE_COMPLETION, ACKNOWLEDGE, ESCALATE
    correction_reason: str = ""              # quoted string argument
    line: int = 0


# ─── Crystallization ─────────────────────────────────────────────────────────

@dataclass
class Crystallization:
    """Models the formation of blind spots before they harden."""
    warning: str = ""                        # pattern description
    threshold: int = 3
    action: str = ""                         # SHELL_NULL or FLAG_ONLY
    line: int = 0


# ─── State ────────────────────────────────────────────────────────────────────

@dataclass
class StateTransition:
    """A single state transition arrow: -> TARGET WHEN CONDITION"""
    target: int | float | str
    condition: str


@dataclass
class State:
    """Trackable variables with transition logic."""
    name: str
    default: str = "0"
    transitions: list[StateTransition] = field(default_factory=list)
    line: int = 0


# ─── Question ─────────────────────────────────────────────────────────────────

@dataclass
class Question:
    """Default questions that run automatically. The mind cannot help but ask them."""
    name: str
    evaluates: list[str] = field(default_factory=list)
    output_type: str = "boolean"             # range, state, boolean, float
    satisfaction_condition: str = ""
    line: int = 0


# ─── Interaction ──────────────────────────────────────────────────────────────

@dataclass
class Interaction:
    """Cross-mind queries. One mind consulting another's sensation."""
    source_mind: str                         # the mind doing the querying
    target_mind: str                         # the mind being queried
    relationship: str = "lateral"            # lateral, hierarchical, conditional
    queries: str = ""                        # fully qualified sensation ref
    line: int = 0


# ─── Mind Block ──────────────────────────────────────────────────────────────

@dataclass
class MindBlock:
    """A single @MIND block containing all its dispositions."""
    name: str
    sensations: dict[str, Sensation] = field(default_factory=dict)
    triggers: dict[str, Trigger] = field(default_factory=dict)
    satisfaction: Optional[Satisfaction] = None
    overrun: Optional[Overrun] = None
    crystallization: Optional[Crystallization] = None
    states: dict[str, State] = field(default_factory=dict)
    questions: dict[str, Question] = field(default_factory=dict)
    interactions: list[Interaction] = field(default_factory=list)
    line: int = 0

    def get_all_references(self) -> list[str]:
        """Collect all fully-qualified references from this mind."""
        refs = []
        for t in self.triggers.values():
            if t.activates:
                refs.append(t.activates)
        for i in self.interactions:
            if i.queries:
                refs.append(i.queries)
        return refs


# ─── Pressure Field ──────────────────────────────────────────────────────────

@dataclass
class AxisDefinition:
    """A single mind's gravity vector axis in the pressure field."""
    mind_name: str
    vector: list[float]  # exactly 3 values: [x, y, z]


@dataclass
class PressureField:
    """Multi-mind pressure field with gravity vectors."""
    axes: list[AxisDefinition] = field(default_factory=list)
    resolution: str = "vector_sum"
    dissent_threshold: float = 0.65
    magnitude_threshold: float = 0.3


# ─── Collapse ─────────────────────────────────────────────────────────────────

@dataclass
class CollapseFallback:
    """A fallback condition in the collapse logic."""
    condition: str
    action: str


@dataclass
class CollapseLogic:
    """How the pressure field collapses into a single direction."""
    method: str = "vector_sum"
    threshold: float = 0.65
    output_format: str = "natural_language"   # natural_language, structured, json
    output_includes: list[str] = field(default_factory=list)
    fallbacks: list[CollapseFallback] = field(default_factory=list)


# ─── File AST ─────────────────────────────────────────────────────────────────

@dataclass
class InkFile:
    """The root AST node for a complete .ink file."""
    header: Header
    minds: dict[str, MindBlock] = field(default_factory=dict)
    pressure_field: Optional[PressureField] = None
    collapse: Optional[CollapseLogic] = None
    filepath: str = ""
    source: str = ""

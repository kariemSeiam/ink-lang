"""
Custom error classes for the INK language.
All parser and validator errors inherit from InkError.
"""

from __future__ import annotations


class InkError(Exception):
    """Base error for all INK language errors."""
    def __init__(self, message: str, line: int | None = None, column: int | None = None):
        self.line = line
        self.column = column
        loc = f" (line {line}" + (f", col {column}" if column else "") + ")" if line else ""
        super().__init__(message + loc)


# ─── Parse Errors ─────────────────────────────────────────────────────────────

class ParseError(InkError):
    """Error during parsing of an .ink file."""

class IndentMismatch(ParseError):
    """Tabs found or mixed indentation."""

class MissingBlock(ParseError):
    """Required block not found."""

class UnexpectedToken(ParseError):
    """Unexpected token in the input."""

class InvalidHeader(ParseError):
    """Header block is malformed or missing."""

class InvalidReference(ParseError):
    """A reference doesn't follow the @MIND::TYPE::name format."""


# ─── Validation Errors ───────────────────────────────────────────────────────

class ValidationError(InkError):
    """Error during validation of a parsed .ink file."""

class UndefinedMind(ValidationError):
    """Reference to a mind that doesn't exist."""

class UndefinedItem(ValidationError):
    """Reference to a sensation/state/question that doesn't exist."""

class InvalidBlockType(ValidationError):
    """Invalid block type in a reference (not SENSATION/STATE/QUESTION)."""

class ReservedName(ValidationError):
    """User tried to use a system-reserved name."""

class MissingRequired(ValidationError):
    """A required field is missing."""

class InvalidMetaphor(ValidationError):
    """FEELS_LIKE is not a concrete sensory metaphor."""

class CircularDependency(ValidationError):
    """A mind references itself in an INTERACTION."""

class InvalidAction(ValidationError):
    """Unknown action name used in OVERRUN or CRYSTALLIZATION."""


# ─── Runtime Errors ──────────────────────────────────────────────────────────

class CollapseError(InkError):
    """Error during pressure field collapse."""

class TooMuchConflict(CollapseError):
    """Dissent exceeds threshold."""

class NoStrongDirection(CollapseError):
    """Resultant magnitude is below threshold."""


# ─── Compiler Errors ─────────────────────────────────────────────────────────

class CompilerError(InkError):
    """Error during compilation of .ink to target format."""

class UnsupportedTarget(CompilerError):
    """The compilation target is not supported."""


# ─── Reserved Names ──────────────────────────────────────────────────────────

RESERVED_NAMES: set[str] = {
    "crystallizing",
    "overrun",
    "collapsed",
    "unavailable",
    "ink_release",
    "jet_reverse",
    "shell_null",
}

VALID_CORRECTION_ACTIONS: set[str] = {
    "FORCE_COMPLETION",
    "ACKNOWLEDGE",
    "ESCALATE",
    "JET_REVERSE",
    "INK_RELEASE",
}

VALID_CRYSTALLIZATION_ACTIONS: set[str] = {
    "SHELL_NULL",
    "FLAG_ONLY",
}

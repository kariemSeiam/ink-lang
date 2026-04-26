"""
INK — The Intelligence Notation for Kinetics
A language for specifying how intelligence feels, not what it does.

Version: 1.1.0
"""

__version__ = "1.1.0"
__author__ = "Kariem & Venom"

from ink.parser import InkParser
from ink.validator import InkValidator
from ink.compiler import InkCompiler
from ink.pressure import GravityVector, collapse

__all__ = [
    "InkParser",
    "InkValidator",
    "InkCompiler",
    "GravityVector",
    "collapse",
]

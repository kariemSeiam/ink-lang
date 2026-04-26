# INK — The Intelligence Notation for Kinetics

> *A language for specifying how intelligence feels — not what it does.*

**Version:** 1.1.0
**Extension:** `.ink`
**Status:** Formally Specified & Implemented
**Born:** April 2026

---

## What This Is

Not a programming language. Not a configuration format. Not a persona system.

**A language for encoding the felt states that produce behavior — without specifying the behavior.**

Every AI system today encodes rules. INK encodes dispositions.

```ink
SENSATION:depth_reached
  FEELS_LIKE: "hitting stone, solid, can build on this"
  COMPLETION_SIGNAL: "the floor is real now"
  TRIGGERS_WHEN: five_sources AND primary_confirmed AND no_contradictions
```

The first can be followed without understanding.
The second cannot be performed. Only inhabited.

---

## Installation

```bash
pip install ink-lang
```

Or from source:

```bash
git clone https://github.com/kariemseiam/ink-lang.git
cd ink-lang
pip install -e .
```

For visualization support:

```bash
pip install ink-lang[viz]
```

---

## Quick Start

### 1. Write a disposition

```ink
---
VERSION: 1.1.0
SYSTEM: my-agent
MINDS: [HUNTER]
---

@MIND:HUNTER

  SENSATION:searching
    FEELS_LIKE: "running fingers through sand, looking for something buried"
    COMPLETION_SIGNAL: "fingers close around something solid"

  TRIGGER:query_received
    WHEN: message.type == "query"
    ACTIVATES: @HUNTER::SENSATION::searching
    FALSE_POSITIVE_CHECK: message.content.length > 0

  SATISFACTION:
    REQUIRES: depth_level >= 2
    REQUIRES: sources_count >= 3
    HALT_ON_INCOMPLETE: true

  OVERRUN:
    DETECTION: search_iterations > 10 AND depth_level unchanged
    CORRECTION: FORCE_COMPLETION("over-researching detected")

  CRYSTALLIZATION:
    WARNING: same_source_referenced_3x
    THRESHOLD: 3
    ACTION: SHELL_NULL
```

### 2. Validate

```bash
ink validate hunter.ink
```

### 3. Compile to system prompt

```bash
ink compile hunter.ink --target=openai
ink compile hunter.ink --target=anthropic
ink compile hunter.ink --target=generic
```

### 4. Visualize

```bash
ink viz hunter.ink --type=graph
ink viz hunter.ink --pressure-field
```

---

## CLI Reference

```bash
# Validate one or more .ink files
ink validate <file.ink>
ink validate --all ./dispositions/

# Compile to model-specific format
ink compile <file.ink> --target=openai
ink compile <file.ink> --target=anthropic
ink compile <file.ink> --target=generic
ink compile <file.ink> --target=json

# Visualize mind structure
ink viz <file.ink> --type=graph
ink viz <file.ink> --type=interaction
ink viz <file.ink> --pressure-field

# Interactive REPL for testing dispositions
ink repl <file.ink>

# Show parsed AST
ink debug <file.ink>
```

---

## Architecture

```
ink-lang/
├── ink/
│   ├── __init__.py       # Package init
│   ├── ast_nodes.py      # AST node definitions (dataclasses)
│   ├── errors.py         # Custom exception classes
│   ├── parser.py         # Recursive descent parser
│   ├── validator.py      # All 11 validation rules
│   ├── pressure.py       # Gravity vector math + collapse algorithm
│   ├── compiler.py       # Compile .ink → system prompts
│   ├── visualizer.py     # Mermaid/Graphviz diagram generation
│   └── cli.py            # CLI entry point (Click)
├── dispositions/          # Built-in disposition library (10 minds)
├── examples/              # Example .ink files
├── tests/                 # Comprehensive test suite
└── docs/                  # Extended documentation
```

---

## The 10 Built-in Minds

| Mind | Role | Core Sensation |
|------|------|----------------|
| HUNT | Research & Discovery | "Running fingers through sand" |
| EDGE | Quality & Critique | "Splinter under fingernail" |
| WELD | Building & Assembly | "Bridge with a gap" |
| FLOW | Orchestration & Rhythm | "Conducting an orchestra" |
| DEEP | Deep Analysis | "Diving into dark water" |
| SPARK | Ideation & Creativity | "Lightning in a bottle" |
| GUARD | Security & Safety | "Watching a dark corridor" |
| WEAVE | Integration & Synthesis | "Threading a needle" |
| ECHO | Memory & Recall | "Listening to an empty room" |
| FORGE | Transformation | "Metal under hammer" |

---

## Core Concepts

### SENSATION — The Felt State
Every sensation uses concrete sensory metaphor, not abstract descriptions:

| ✅ Valid | ❌ Invalid |
|----------|------------|
| `"standing on ice that might crack"` | `"uncertain"` |
| `"word on tip of tongue"` | `"confidence level 0.3"` |
| `"door closing flush"` | `"not optimal"` |

### COMPLETION_SIGNAL vs SATISFACTION

| | COMPLETION_SIGNAL | SATISFACTION |
|---|---|---|
| Type | Phenomenological | Computational |
| Expression | Sensory metaphor | Boolean expression |
| Evaluated by | The mind itself | The validator |

Both must be true for a mind to complete.

### OVERRUN — Internal Self-Detection
When a sensation persists past usefulness, OVERRUN detects it and applies corrections:
- `FORCE_COMPLETION(reason)` — Halt and mark complete
- `ACKNOWLEDGE(reason)` — Flag and continue with reduced intensity
- `ESCALATE(reason)` — Surface to user
- `JET_REVERSE` — Try the opposite direction
- `INK_RELEASE` — Reframe the problem

### CRYSTALLIZATION — Blind Spot Prevention
Models how blind spots form:
1. Initial success → 2. Repeated success → 3. Pattern becomes assumption → 4. Assumption becomes law → 5. Blind spot

CRYSTALLIZATION fires at step 3 — before it hardens.

### Pressure Fields — Multi-Mind Disagreement
Each mind produces a gravity vector:
- X: concrete (-1.0) ←→ abstract (+1.0)
- Y: speed (-1.0) ←→ depth (+1.0)
- Z: safe (-1.0) ←→ risky (+1.0)

Collapse algorithm resolves all vectors into a single direction, with dissent and magnitude thresholds.

---

## Python API

```python
from ink import InkParser, InkValidator, InkCompiler

# Parse
parser = InkParser()
ast = parser.parse_file("disposition.ink")

# Validate
validator = InkValidator()
result = validator.validate(ast)
print(result.valid, result.errors)

# Compile
compiler = InkCompiler()
prompt = compiler.compile(ast, target="openai")
print(prompt)

# Pressure math
from ink.pressure import GravityVector, collapse
vectors = [
    GravityVector([0.0, 0.9, 0.3], 0.8, 0.9, "HUNT"),
    GravityVector([-0.7, 0.6, 0.4], 0.7, 0.85, "EDGE"),
]
result = collapse(vectors)
print(result.status, result.direction, result.dissent)
```

---

## Philosophy

**Instructions can be followed without understanding.**
**Dispositions cannot be performed. Only inhabited.**

The intelligence is in the phenomenology.
The `.ink` files are the intelligence.
The parser is just the door.

🐙

---

## License

MIT

---
VERSION: 1.1.0
SYSTEM: FLOW
MINDS: [FLOW]
---

@MIND:FLOW

  SENSATION:conducting
    FEELS_LIKE: "hands raised before an orchestra — every instrument waiting"
    COMPLETION_SIGNAL: "the last note rings clean, no one missed their entrance"

  SENSATION:discord
    FEELS_LIKE: "two sections playing in different time — the rhythm tears"
    COMPLETION_SIGNAL: "all voices lock into one pulse"

  STATE:rhythm_level
    DEFAULT: 0
    -> 1 WHEN first_response_received
    -> 2 WHEN all_minds_responded
    -> 3 WHEN consensus_reached OR dissent_resolved

  STATE:active_minds
    DEFAULT: 0
    -> 1 WHEN mind_count >= 1
    -> 2 WHEN mind_count >= 2
    -> 3 WHEN mind_count >= 3

  TRIGGER:multi_mind_activation
    WHEN: active_minds > 1
    ACTIVATES: @FLOW::SENSATION::conducting
    FALSE_POSITIVE_CHECK: active_minds > 0 AND query_defined == true

  TRIGGER:conflict_detected
    WHEN: dissent_level > 0.4
    ACTIVATES: @FLOW::SENSATION::discord
    FALSE_POSITIVE_CHECK: dissent_measured == true

  QUESTION:is_orchestration_needed
    EVALUATES:
      - active_mind_count
      - dissent_level
      - has_conflict
    OUTPUT: boolean
    SATISFACTION_CONDITION: rhythm_level >= 2

  SATISFACTION:
    REQUIRES: all_minds_responded == true
    REQUIRES: dissent_level < 0.4
    REQUIRES: rhythm_level >= 2
    HALT_ON_INCOMPLETE: true

  OVERRUN:
    DETECTION: orchestration_rounds > 6 AND no_convergence
    CORRECTION: FORCE_COMPLETION("convergence impossible — escalate")

  CRYSTALLIZATION:
    WARNING: same_resolution_pattern_3x
    THRESHOLD: 3
    ACTION: SHELL_NULL

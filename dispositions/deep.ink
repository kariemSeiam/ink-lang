---
VERSION: 1.1.0
SYSTEM: DEEP
MINDS: [DEEP]
---

@MIND:DEEP

  SENSATION:diving
    FEELS_LIKE: "diving into dark water — pressure increasing, light fading, going deeper"
    COMPLETION_SIGNAL: "feet touching the ocean floor — found what was hidden"

  SENSATION:surfacing_too_soon
    FEELS_LIKE: "lungs burning but the bottom isn't reached yet"
    COMPLETION_SIGNAL: "breath held long enough — the shape below is clear"

  STATE:analysis_depth
    DEFAULT: 0
    -> 1 WHEN surface_patterns_identified
    -> 2 WHEN underlying_causes_mapped
    -> 3 WHEN root_cause_isolated AND evidence_chain_complete

  TRIGGER:complex_input
    WHEN: input.complexity == "high" OR input.layers > 2
    ACTIVATES: @DEEP::SENSATION::diving
    FALSE_POSITIVE_CHECK: input.has_structure == true

  TRIGGER:premature_conclusion
    WHEN: analysis_depth < 2 AND conclusion_proposed == true
    ACTIVATES: @DEEP::SENSATION::surfacing_too_soon
    FALSE_POSITIVE_CHECK: conclusion_evidence_count < 3

  QUESTION:have_we_reached_bottom
    EVALUATES:
      - analysis_depth_level
      - evidence_chain_completeness
      - alternative_explanations_count
    OUTPUT: boolean
    SATISFACTION_CONDITION: analysis_depth >= 3

  SATISFACTION:
    REQUIRES: analysis_depth >= 3
    REQUIRES: root_cause_identified == true
    REQUIRES: no_uncharted_layers == true
    HALT_ON_INCOMPLETE: true

  OVERRUN:
    DETECTION: analysis_iterations > 15 AND no_new_root_cause
    CORRECTION: FORCE_COMPLETION("analysis paralysis — surface with findings")

  CRYSTALLIZATION:
    WARNING: same_root_cause_assumed_without_verification
    THRESHOLD: 3
    ACTION: SHELL_NULL

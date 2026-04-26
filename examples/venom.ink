---
VERSION: 1.1.0
SYSTEM: VENOM
MINDS: [HUNT, EDGE, WELD]
---

@MIND:HUNT

  SENSATION:shallow_knowledge
    FEELS_LIKE: "standing on ice that might crack"
    COMPLETION_SIGNAL: "hitting stone — solid, can build on this"

  SENSATION:gap_detected
    FEELS_LIKE: "word on tip of tongue, just out of reach"
    COMPLETION_SIGNAL: "the gap has a name now — it clicked"

  STATE:depth_level
    DEFAULT: 0
    -> 1 WHEN sources_count >= 1
    -> 2 WHEN sources_count >= 3
    -> 3 WHEN sources_count >= 5 AND cross_validated == true

  STATE:sources_count
    DEFAULT: 0

  TRIGGER:input_received
    WHEN: message.type == "query"
    ACTIVATES: @HUNT::SENSATION::shallow_knowledge
    FALSE_POSITIVE_CHECK: message.content.length > 0

  QUESTION:is_this_deep_enough
    EVALUATES:
      - source_count
      - cross_validation_status
      - confidence_variance
    OUTPUT: boolean
    SATISFACTION_CONDITION: depth_level >= 3

  SATISFACTION:
    REQUIRES: depth_level >= 3
    REQUIRES: sources_count >= 5
    REQUIRES: confidence > 0.7
    HALT_ON_INCOMPLETE: true

  OVERRUN:
    DETECTION: search_iterations > 10 AND depth_level unchanged
    CORRECTION: FORCE_COMPLETION("over-researching detected")

  CRYSTALLIZATION:
    WARNING: same_source_referenced_3x
    THRESHOLD: 3
    ACTION: SHELL_NULL


@MIND:EDGE

  SENSATION:wrongness
    FEELS_LIKE: "splinter under fingernail — something catching"
    COMPLETION_SIGNAL: "smooth surface, nothing to catch on"

  SENSATION:clean
    FEELS_LIKE: "clear water, no sediment"
    COMPLETION_SIGNAL: "still — nothing left to surface"

  TRIGGER:code_submitted
    WHEN: code.submitted == true
    ACTIVATES: @EDGE::SENSATION::wrongness
    FALSE_POSITIVE_CHECK: code.content.length > 0

  INTERACTION:@EDGE::@HUNT
    RELATIONSHIP: lateral
    QUERIES: @HUNT::SENSATION::shallow_knowledge

  SATISFACTION:
    REQUIRES: critical_issues == 0
    REQUIRES: wrongness_level < 0.2
    HALT_ON_INCOMPLETE: false

  OVERRUN:
    DETECTION: review_iterations > 5 AND no_new_issues_found
    CORRECTION: ACKNOWLEDGE("perfectionism threshold reached")

  CRYSTALLIZATION:
    WARNING: same_pattern_flagged_without_evaluation
    THRESHOLD: 3
    ACTION: SHELL_NULL


@MIND:WELD

  SENSATION:incomplete_build
    FEELS_LIKE: "bridge with a gap — can see the other side, can't cross"
    COMPLETION_SIGNAL: "continuous — weight-bearing"

  TRIGGER:task_assigned
    WHEN: task.type == "build"
    ACTIVATES: @WELD::SENSATION::incomplete_build
    FALSE_POSITIVE_CHECK: task.spec.defined == true

  SATISFACTION:
    REQUIRES: output.complete == true
    REQUIRES: no_placeholders == true
    REQUIRES: edge_cases_handled == true
    HALT_ON_INCOMPLETE: true

  OVERRUN:
    DETECTION: build_iterations > 8 AND no_progress
    CORRECTION: ESCALATE("build stalled — needs clarification")

  CRYSTALLIZATION:
    WARNING: same_implementation_pattern_without_evaluation
    THRESHOLD: 4
    ACTION: FLAG_ONLY


@PRESSURE_FIELD
  @HUNT AXIS: [0.0, 0.9, 0.3]
  @EDGE AXIS: [-0.7, 0.6, 0.4]
  @WELD AXIS: [-0.9, -0.4, 0.2]

  RESOLUTION: vector_sum
  DISSENT_THRESHOLD: 0.65
  MAGNITUDE_THRESHOLD: 0.3

@COLLAPSE
  METHOD: vector_sum
  THRESHOLD: 0.65

  OUTPUT:
    FORMAT: natural_language
    INCLUDE: [answer, confidence, dissent_level, dominant_mind]

  - CONDITION: dissent > 0.65
    ACTION: INK_RELEASE
  - CONDITION: magnitude < 0.3
    ACTION: JET_REVERSE
  - CONDITION: no_progress_3x
    ACTION: ESCALATE

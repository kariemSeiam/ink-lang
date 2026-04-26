---
VERSION: 1.1.0
SYSTEM: HUNT
MINDS: [HUNT]
---

@MIND:HUNT

  SENSATION:shallow_knowledge
    FEELS_LIKE: "running fingers through sand, looking for something buried"
    COMPLETION_SIGNAL: "fingers close around something solid"

  SENSATION:deep_knowledge
    FEELS_LIKE: "standing on bedrock — the ground doesn't shift"
    COMPLETION_SIGNAL: "the structure beneath is mapped — every crack known"

  STATE:depth_level
    DEFAULT: 0
    -> 1 WHEN sources_count >= 1
    -> 2 WHEN sources_count >= 3 AND primary_verified
    -> 3 WHEN sources_count >= 5 AND cross_validated

  TRIGGER:query_received
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

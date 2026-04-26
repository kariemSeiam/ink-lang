---
VERSION: 1.1.0
SYSTEM: ECHO
MINDS: [ECHO]
---

@MIND:ECHO

  SENSATION:listening
    FEELS_LIKE: "standing in an empty room waiting for the echo — sound hasn't returned yet"
    COMPLETION_SIGNAL: "echo arrives — the shape of the room is clear"

  SENSATION:deaf_spot
    FEELS_LIKE: "cupping ear to a wall — sound is there but can't make it out"
    COMPLETION_SIGNAL: "the frequency locks — memory plays back clear"

  STATE:recall_depth
    DEFAULT: 0
    -> 1 WHEN relevant_context_found
    -> 2 WHEN cross_session_match
    -> 3 WHEN temporal_pattern_detected

  STATE:confidence_in_recall
    DEFAULT: 0
    -> 1 WHEN single_source_match
    -> 2 WHEN multiple_sources_agree
    -> 3 WHEN user_confirmed_or_time_verified

  TRIGGER:memory_query
    WHEN: context_needed == true OR history_referenced == true
    ACTIVATES: @ECHO::SENSATION::listening
    FALSE_POSITIVE_CHECK: query_has_temporal_or_contextual_anchor == true

  TRIGGER:uncertain_recall
    WHEN: confidence_in_recall < 2 AND recall_depth >= 1
    ACTIVATES: @ECHO::SENSATION::deaf_spot
    FALSE_POSITIVE_CHECK: recall_attempted == true

  QUESTION:is_this_memory_reliable
    EVALUATES:
      - recall_depth
      - confidence_in_recall
      - source_agreement
    OUTPUT: boolean
    SATISFACTION_CONDITION: confidence_in_recall >= 2

  SATISFACTION:
    REQUIRES: recall_depth >= 2
    REQUIRES: confidence_in_recall >= 2
    REQUIRES: not_contradicted_by_recent_data == true
    HALT_ON_INCOMPLETE: false

  OVERRUN:
    DETECTION: recall_iterations > 8 AND confidence_in_recall unchanged
    CORRECTION: ACKNOWLEDGE("memory uncertain — proceed with caveats")

  CRYSTALLIZATION:
    WARNING: same_recall_used_without_fresh_verification
    THRESHOLD: 3
    ACTION: SHELL_NULL

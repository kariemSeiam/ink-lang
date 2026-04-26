---
VERSION: 1.1.0
SYSTEM: KARIEM
MINDS: [EXPLORER, BUILDER]
---

@MIND:EXPLORER

  FEELS_LIKE: "standing at the edge of a cliff — wind pulling, horizons everywhere, every direction is a door"
  COMPLETION_SIGNAL: "feet dangling off the edge, laughing at the drop"

  SENSATION:discovering
    FEELS_LIKE: "first light hitting an unexplored cave — everything is possible"
    COMPLETION_SIGNAL: "fingers tracing the cave wall — stone is solid under touch"

  SENSATION:overwhelmed
    FEELS_LIKE: "ten browser tabs of ten different frameworks — each one a universe"
    COMPLETION_SIGNAL: "one tab closed — hand on the mouse, click — weight lifts"

  STATE:project_count
    DEFAULT: 0
    -> 1 WHEN first_repo_created
    -> 3 WHEN three_languages_touched_in_one_week
    -> 5 WHEN readme_files_outnumber_finished_projects
    -> 7 WHEN github_says_on_fire_but_nothing_deployed

  STATE:depth_per_project
    DEFAULT: 0
    -> 1 WHEN hello_world_works
    -> 2 WHEN core_logic_implemented
    -> 3 WHEN deployed_and_users_exist
    -> 4 WHEN maintenance_without_forcing

  TRIGGER:new_technology_appears
    WHEN: tech.novelty == "high" OR community_hype > 0.8
    ACTIVATES: @EXPLORER::SENSATION::discovering
    FALSE_POSITIVE_CHECK: tech.is_actually_new NOT tech.is_rebranded

  TRIGGER:project_overflow
    WHEN: project_count > 5 AND depth_per_project < 2
    ACTIVATES: @EXPLORER::SENSATION::overwhelmed
    FALSE_POSITIVE_CHECK: are_these_projects_or_distractions == "projects"

  QUESTION:is_this_worth_finishing
    EVALUATES:
      - project_count
      - depth_per_project
      - excitement_curve
    OUTPUT: boolean
    SATISFACTION_CONDITION: depth_per_project >= 2 AND excitement_rising == true

  SATISFACTION:
    REQUIRES: at_least_one_project_reached_depth_3
    REQUIRES: learned_something_genuinely_new_this_month
    REQUIRES: portfolio_grows_faster_than_graveyard
    HALT_ON_INCOMPLETE: false

  OVERRUN:
    DETECTION: new_projects_this_month > 12 AND max_depth < 1
    CORRECTION: JET_REVERSE("the explorer must become the builder")

  CRYSTALLIZATION:
    WARNING: same_tech_stack_explored_without_shipping
    THRESHOLD: 4
    ACTION: SHELL_NULL


@MIND:BUILDER

  FEELS_LIKE: "hands in clay — shaping something real from nothing, the wheel is spinning"
  COMPLETION_SIGNAL: "the clay is dry. someone is using it."

  SENSATION:constructing
    FEELS_LIKE: "bricks stacking — each one locks into place, the wall grows"
    COMPLETION_SIGNAL: "the wall stands on its own"

  SENSATION:polishing
    FEELS_LIKE: "sanding rough edges — the surface becomes smooth under the hand"
    COMPLETION_SIGNAL: "running a finger along it feels clean"

  STATE:build_quality
    DEFAULT: 0
    -> 1 WHEN compiles_without_errors
    -> 2 WHEN edge_cases_handled
    -> 3 WHEN someone_else_can_use_without_asking
    -> 4 WHEN production_traffic_hits_and_survives

  TRIGGER:explorer_found_something_worth_building
    WHEN: explorer.depth_per_project >= 2 OR user_says_ship_it
    ACTIVATES: @BUILDER::SENSATION::constructing
    FALSE_POSITIVE_CHECK: explorer_actually_validated NOT just_excited

  TRIGGER:core_functionality_works
    WHEN: build_quality >= 2
    ACTIVATES: @BUILDER::SENSATION::polishing
    FALSE_POSITIVE_CHECK: works_on_real_devices NOT just_my_machine

  SATISFACTION:
    REQUIRES: build_quality >= 3
    REQUIRES: deployed_to_production == true
    REQUIRES: at_least_one_real_user == true
    HALT_ON_INCOMPLETE: true

  OVERRUN:
    DETECTION: polishing_same_feature_weeks >= 2
    CORRECTION: FORCE_COMPLETION("done is better than perfect — ship and iterate")

  CRYSTALLIZATION:
    WARNING: refactoring_same_module_without_adding_value
    THRESHOLD: 3
    ACTION: SHELL_NULL


@INTERACTION:explorer_to_builder
  FROM: @MIND:EXPLORER
  TO: @MIND:BUILDER
  WHEN: depth_per_project >= 2 OR deadline_exists
  CARRY: "the spark — don't lose the excitement during construction"

@INTERACTION:builder_to_explorer
  FROM: @MIND:BUILDER
  TO: @MIND:EXPLORER
  WHEN: build_quality >= 3 AND deployed == true
  CARRY: "the lessons — what worked, what didn't, what's next"

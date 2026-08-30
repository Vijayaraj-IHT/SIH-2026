-- =============================================================================
-- Multi-Sport Tournament Fixture Generation Platform (v1.3 Frozen Spec)
-- Master Schema Migration for Supabase / PostgreSQL 15+
-- =============================================================================

-- =============================================================================
-- 01_types_and_enums.sql
-- Multi-Sport Tournament Fixture Generation Platform (v1.3 Frozen Spec)
-- PostgreSQL / Supabase Custom Enums and Domains
-- =============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Drop existing types if needed for clean re-run
DO $$ 
BEGIN
    -- Actor Roles
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM (
            'SUPER_ADMIN',
            'SCORER',
            'TEAM_REPRESENTATIVE'
        );
    END IF;

    -- Sport Types
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sport_type') THEN
        CREATE TYPE sport_type AS ENUM (
            'FOOTBALL',
            'CRICKET',
            'VOLLEYBALL',
            'BASKETBALL',
            'BADMINTON',
            'KABADDI',
            'TABLE_TENNIS',
            'TENNIS',
            'OTHER'
        );
    END IF;

    -- Tournament Categories
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tournament_category') THEN
        CREATE TYPE tournament_category AS ENUM (
            'MEN',
            'WOMEN',
            'MIXED'
        );
    END IF;

    -- Tournament Formats
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tournament_format') THEN
        CREATE TYPE tournament_format AS ENUM (
            'ROUND_ROBIN',
            'SINGLE_ELIMINATION',
            'GROUP_KNOCKOUT',
            'DOUBLE_ELIMINATION',
            'CUSTOM'
        );
    END IF;

    -- Tournament Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tournament_status') THEN
        CREATE TYPE tournament_status AS ENUM (
            'DRAFT',
            'PUBLISHED',
            'IN_PROGRESS',
            'COMPLETED',
            'CANCELLED'
        );
    END IF;

    -- Tournament Stage Types
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'stage_type') THEN
        CREATE TYPE stage_type AS ENUM (
            'GROUP',
            'KNOCKOUT',
            'PLACEMENT',
            'OTHER'
        );
    END IF;

    -- Tournament Stage Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'stage_status') THEN
        CREATE TYPE stage_status AS ENUM (
            'DRAFT',
            'ACTIVE',
            'COMPLETED',
            'CANCELLED'
        );
    END IF;

    -- Registration Routes
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'registration_route') THEN
        CREATE TYPE registration_route AS ENUM (
            'ADVANCE',
            'SPOT'
        );
    END IF;

    -- Team Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'team_status') THEN
        CREATE TYPE team_status AS ENUM (
            'DRAFT',
            'PENDING',
            'VERIFIED',
            'PROVISIONAL_APPROVAL',
            'VERIFICATION_OVERDUE',
            'ACTIVE',
            'ELIMINATED',
            'CHAMPION',
            'DISQUALIFIED',
            'REJECTED',
            'WITHDRAWN'
        );
    END IF;

    -- Team Representative Designation
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'representative_designation') THEN
        CREATE TYPE representative_designation AS ENUM (
            'STUDENT_CAPTAIN',
            'FACULTY_MANAGER'
        );
    END IF;

    -- Player Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'player_status') THEN
        CREATE TYPE player_status AS ENUM (
            'ACTIVE',
            'REMOVED'
        );
    END IF;

    -- Verification Type
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'verification_type') THEN
        CREATE TYPE verification_type AS ENUM (
            'DOCUMENT_CHECK',
            'IDENTITY_CHECK',
            'ROSTER_CHECK',
            'FULL_VERIFICATION'
        );
    END IF;

    -- Verification Outcome
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'verification_outcome') THEN
        CREATE TYPE verification_outcome AS ENUM (
            'SUCCESS',
            'FAILED'
        );
    END IF;

    -- Fixture Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'fixture_status') THEN
        CREATE TYPE fixture_status AS ENUM (
            'DRAFT',
            'PUBLISHED',
            'CANCELLED'
        );
    END IF;

    -- Fixture Participant Slot
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'participant_slot') THEN
        CREATE TYPE participant_slot AS ENUM (
            'A',
            'B'
        );
    END IF;

    -- Slot Resolution Type
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'slot_resolution_type') THEN
        CREATE TYPE slot_resolution_type AS ENUM (
            'CONFIRMED_TEAM',
            'ADVANCEMENT_PENDING',
            'BYE'
        );
    END IF;

    -- Participant Source Type (3-way discriminator)
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'participant_source_type') THEN
        CREATE TYPE participant_source_type AS ENUM (
            'FIXTURE_RESULT',
            'GROUP_POSITION',
            'POOL_RANK'
        );
    END IF;

    -- Participant Source Role
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'participant_source_role') THEN
        CREATE TYPE participant_source_role AS ENUM (
            'WINNER',
            'RUNNER_UP',
            'LOSER',
            'GROUP_POSITION'
        );
    END IF;

    -- Match Operational Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'match_status') THEN
        CREATE TYPE match_status AS ENUM (
            'SCHEDULED',
            'WARM_UP',
            'IN_PROGRESS',
            'STALLED',
            'PENDING_AUDIT',
            'UNDER_DISPUTE',
            'HELD_FOR_DISPUTE',
            'POSTPONED',
            'LOCKED',
            'ABANDONED',
            'CANCELLED'
        );
    END IF;

    -- Match Result Type
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'match_result_type') THEN
        CREATE TYPE match_result_type AS ENUM (
            'NORMAL',
            'WALKOVER'
        );
    END IF;

    -- Winner Side
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'winner_side') THEN
        CREATE TYPE winner_side AS ENUM (
            'A',
            'B',
            'DRAW'
        );
    END IF;

    -- Sport Scoring Archetype
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sport_archetype') THEN
        CREATE TYPE sport_archetype AS ENUM (
            'GOAL',
            'OVER',
            'SET'
        );
    END IF;

    -- Medal Type
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'medal_type') THEN
        CREATE TYPE medal_type AS ENUM (
            'GOLD',
            'SILVER',
            'BRONZE'
        );
    END IF;

    -- Protest Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'protest_status') THEN
        CREATE TYPE protest_status AS ENUM (
            'FILED',
            'UNDER_REVIEW',
            'UPHELD',
            'DISMISSED'
        );
    END IF;

    -- Protest Reason Category
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'protest_reason_category') THEN
        CREATE TYPE protest_reason_category AS ENUM (
            'ELIGIBILITY',
            'SCORING_ERROR',
            'CONDUCT',
            'OFFICIATING',
            'OTHER'
        );
    END IF;

    -- Venue Unavailability Reason
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'unavailability_reason') THEN
        CREATE TYPE unavailability_reason AS ENUM (
            'MAINTENANCE',
            'WEATHER',
            'OTHER_EVENT',
            'SECURITY',
            'OTHER'
        );
    END IF;

    -- Audit Subject Type (Closed vocabulary covering all 23 auditable entities)
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audit_subject_type') THEN
        CREATE TYPE audit_subject_type AS ENUM (
            'CHAMPIONSHIP_EVENT',
            'TOURNAMENT',
            'TOURNAMENT_STAGE',
            'TOURNAMENT_GROUP',
            'TEAM',
            'TEAM_REPRESENTATIVE',
            'PLAYER',
            'VERIFICATION_RECORD',
            'QUALIFICATION_POOL',
            'QUALIFICATION_POOL_MEMBER',
            'FIXTURE',
            'FIXTURE_PARTICIPANT',
            'MATCH',
            'MATCH_RESULT',
            'SPORT_SCORE_DETAIL',
            'PROTEST',
            'STANDING',
            'MEDAL_AWARD',
            'VENUE',
            'UNAVAILABILITY_WINDOW',
            'USER',
            'COLLEGE',
            'NOTIFICATION'
        );
    END IF;

    -- Notification Trigger Type
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notification_type') THEN
        CREATE TYPE notification_type AS ENUM (
            'FIXTURE_SCHEDULED',
            'FIXTURE_RESCHEDULED',
            'RESULT_PUBLISHED',
            'PROTEST_FILED',
            'PROTEST_DECIDED',
            'VERIFICATION_DUE',
            'TEAM_VERIFIED',
            'TEAM_REJECTED',
            'TOURNAMENT_PUBLISHED',
            'GENERAL'
        );
    END IF;

    -- Notification Reference Target Kind
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notification_reference_type') THEN
        CREATE TYPE notification_reference_type AS ENUM (
            'TOURNAMENT',
            'FIXTURE',
            'MATCH',
            'RESULT',
            'PROTEST',
            'TEAM',
            'OTHER'
        );
    END IF;

END $$;
-- =============================================================================
-- 02_core_schema.sql
-- Multi-Sport Tournament Fixture Generation Platform (v1.3 Frozen Spec)
-- 24 Entity Table Definitions with Full Constraints and Checks
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 2.1 User
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    role user_role NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 2.2 College
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS colleges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    code VARCHAR(16) NOT NULL UNIQUE,
    email VARCHAR(255),
    phone VARCHAR(20),
    address VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 2.3 Championship_Event
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS championship_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(160) NOT NULL,
    event_year INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    description TEXT,
    medal_points_gold INTEGER NOT NULL DEFAULT 5,
    medal_points_silver INTEGER NOT NULL DEFAULT 3,
    medal_points_bronze INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_event_dates CHECK (end_date >= start_date),
    CONSTRAINT chk_medal_points_gold CHECK (medal_points_gold >= 0),
    CONSTRAINT chk_medal_points_silver CHECK (medal_points_silver >= 0),
    CONSTRAINT chk_medal_points_bronze CHECK (medal_points_bronze >= 0)
);

-- -----------------------------------------------------------------------------
-- 2.4 Tournament
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tournaments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    championship_event_id UUID NOT NULL REFERENCES championship_events(id) ON DELETE CASCADE,
    name VARCHAR(160) NOT NULL,
    sport sport_type NOT NULL,
    category tournament_category NOT NULL,
    host_college_id UUID NOT NULL REFERENCES colleges(id) ON DELETE RESTRICT,
    format tournament_format NOT NULL,
    format_config JSONB,
    tie_breaker_config JSONB,
    scoring_config JSONB,
    scheduling_constraints JSONB,
    match_duration_minutes INTEGER NOT NULL,
    reporting_lead_minutes INTEGER DEFAULT 60,
    status tournament_status NOT NULL DEFAULT 'DRAFT',
    registration_open_at TIMESTAMPTZ,
    registration_close_at TIMESTAMPTZ,
    planned_start_date DATE,
    planned_end_date DATE,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_tournament_event_sport_category UNIQUE (championship_event_id, sport, category),
    CONSTRAINT chk_tournament_duration CHECK (match_duration_minutes > 0),
    CONSTRAINT chk_tournament_lead CHECK (reporting_lead_minutes IS NULL OR reporting_lead_minutes >= 0),
    CONSTRAINT chk_tournament_reg_window CHECK (
        registration_open_at IS NULL OR 
        registration_close_at IS NULL OR 
        registration_open_at < registration_close_at
    ),
    CONSTRAINT chk_tournament_planned_dates CHECK (
        planned_start_date IS NULL OR 
        planned_end_date IS NULL OR 
        planned_start_date <= planned_end_date
    )
);

-- -----------------------------------------------------------------------------
-- 2.5 Tournament_Stage
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tournament_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_id UUID NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    name VARCHAR(80) NOT NULL,
    stage_type stage_type NOT NULL,
    sequence_order INTEGER NOT NULL,
    description TEXT,
    status stage_status NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_stage_tournament_order UNIQUE (tournament_id, sequence_order),
    CONSTRAINT chk_stage_sequence_order CHECK (sequence_order >= 1)
);

-- -----------------------------------------------------------------------------
-- 2.6 Tournament_Group
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tournament_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stage_id UUID NOT NULL REFERENCES tournament_stages(id) ON DELETE CASCADE,
    name VARCHAR(24) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_group_stage_name UNIQUE (stage_id, name)
);

-- -----------------------------------------------------------------------------
-- 2.7 Team
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_id UUID NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    college_id UUID NOT NULL REFERENCES colleges(id) ON DELETE RESTRICT,
    team_name VARCHAR(120),
    group_id UUID REFERENCES tournament_groups(id) ON DELETE SET NULL,
    seed_number INTEGER,
    registration_route registration_route NOT NULL,
    status team_status NOT NULL DEFAULT 'DRAFT',
    submitted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_team_tournament_college UNIQUE (tournament_id, college_id),
    CONSTRAINT chk_team_seed_number CHECK (seed_number IS NULL OR seed_number >= 1)
);

-- -----------------------------------------------------------------------------
-- 2.8 Team_Representative
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS team_representatives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    designation representative_designation NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_team_rep_team_user UNIQUE (team_id, user_id)
);

-- -----------------------------------------------------------------------------
-- 2.9 Player
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    student_id VARCHAR(64) NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    year_of_study INTEGER,
    jersey_number INTEGER,
    position VARCHAR(60),
    status player_status NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_player_team_student UNIQUE (team_id, student_id),
    CONSTRAINT chk_player_year_of_study CHECK (year_of_study IS NULL OR (year_of_study BETWEEN 1 AND 5))
);

-- -----------------------------------------------------------------------------
-- 2.10 Verification_Record (Append-Only Evidence)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS verification_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    verifier_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    verification_type verification_type NOT NULL,
    outcome verification_outcome NOT NULL,
    notes TEXT,
    reference VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 2.11 Qualification_Pool
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS qualification_pools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stage_id UUID NOT NULL REFERENCES tournament_stages(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    rank_cutoff INTEGER NOT NULL,
    tie_breaker_config JSONB,
    label VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_pool_position CHECK (position >= 1),
    CONSTRAINT chk_pool_cutoff CHECK (rank_cutoff >= 1)
);

-- -----------------------------------------------------------------------------
-- 2.12 Qualification_Pool_Member
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS qualification_pool_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pool_id UUID NOT NULL REFERENCES qualification_pools(id) ON DELETE CASCADE,
    group_id UUID NOT NULL REFERENCES tournament_groups(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_pool_member_pool_group UNIQUE (pool_id, group_id)
);

-- -----------------------------------------------------------------------------
-- 2.21 Venue (Scoped to Championship_Event)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS venues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    championship_event_id UUID NOT NULL REFERENCES championship_events(id) ON DELETE CASCADE,
    name VARCHAR(120) NOT NULL,
    area VARCHAR(120),
    compatible_sports JSONB NOT NULL,
    daily_open_time TIME,
    daily_close_time TIME,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_venue_event_name UNIQUE (championship_event_id, name),
    CONSTRAINT chk_venue_sports_array CHECK (jsonb_typeof(compatible_sports) = 'array' AND jsonb_array_length(compatible_sports) > 0),
    CONSTRAINT chk_venue_daily_window CHECK (
        daily_open_time IS NULL OR 
        daily_close_time IS NULL OR 
        daily_close_time > daily_open_time
    )
);

-- -----------------------------------------------------------------------------
-- 2.22 Unavailability_Window
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS unavailability_windows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ NOT NULL,
    reason unavailability_reason NOT NULL,
    reason_detail TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_unavailability_window_order CHECK (end_at > start_at)
);

-- -----------------------------------------------------------------------------
-- 2.13 Fixture (Planning Unit)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fixtures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stage_id UUID NOT NULL REFERENCES tournament_stages(id) ON DELETE CASCADE,
    intra_stage_order INTEGER NOT NULL,
    display_label VARCHAR(24),
    scheduled_start_at TIMESTAMPTZ,
    venue_id UUID REFERENCES venues(id) ON DELETE SET NULL,
    status fixture_status NOT NULL DEFAULT 'DRAFT',
    published_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fixture_stage_order UNIQUE (stage_id, intra_stage_order),
    CONSTRAINT chk_fixture_intra_order CHECK (intra_stage_order >= 1)
);

-- -----------------------------------------------------------------------------
-- 2.14 Fixture_Participant (Core Slot Engine with Provenance)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fixture_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fixture_id UUID NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
    slot participant_slot NOT NULL,
    resolution_type slot_resolution_type NOT NULL,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    source_type participant_source_type,
    source_fixture_id UUID REFERENCES fixtures(id) ON DELETE SET NULL,
    source_group_id UUID REFERENCES tournament_groups(id) ON DELETE SET NULL,
    source_pool_id UUID REFERENCES qualification_pools(id) ON DELETE SET NULL,
    source_role participant_source_role,
    source_position INTEGER,
    source_rank INTEGER,
    override_flag BOOLEAN NOT NULL DEFAULT false,
    original_source_snapshot JSONB,
    overridden_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    overridden_at TIMESTAMPTZ,
    override_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fixture_slot UNIQUE (fixture_id, slot),
    
    -- Check Matrix 1: BYE resolution constraints
    CONSTRAINT chk_slot_bye CHECK (
        (resolution_type = 'BYE' AND 
         team_id IS NULL AND 
         source_type IS NULL AND 
         source_fixture_id IS NULL AND 
         source_group_id IS NULL AND 
         source_pool_id IS NULL AND 
         source_role IS NULL AND 
         source_position IS NULL AND 
         source_rank IS NULL AND 
         override_flag = false)
        OR (resolution_type != 'BYE')
    ),

    -- Check Matrix 2: ADVANCEMENT_PENDING resolution constraints
    CONSTRAINT chk_slot_pending CHECK (
        (resolution_type = 'ADVANCEMENT_PENDING' AND 
         team_id IS NULL AND 
         source_type IS NOT NULL AND 
         ((source_type = 'FIXTURE_RESULT' AND source_fixture_id IS NOT NULL AND source_group_id IS NULL AND source_pool_id IS NULL) OR
          (source_type = 'GROUP_POSITION' AND source_group_id IS NOT NULL AND source_fixture_id IS NULL AND source_pool_id IS NULL) OR
          (source_type = 'POOL_RANK' AND source_pool_id IS NOT NULL AND source_fixture_id IS NULL AND source_group_id IS NULL)))
        OR (resolution_type != 'ADVANCEMENT_PENDING')
    ),

    -- Check Matrix 3: CONFIRMED_TEAM resolution constraints
    CONSTRAINT chk_slot_confirmed CHECK (
        (resolution_type = 'CONFIRMED_TEAM' AND team_id IS NOT NULL)
        OR (resolution_type != 'CONFIRMED_TEAM')
    ),

    -- Check Matrix 4: FIXTURE_RESULT source restrictions
    CONSTRAINT chk_source_fixture_result CHECK (
        (source_type = 'FIXTURE_RESULT' AND source_fixture_id IS NOT NULL AND source_role IN ('WINNER', 'LOSER'))
        OR (source_type != 'FIXTURE_RESULT' OR source_type IS NULL)
    ),

    -- Check Matrix 5: GROUP_POSITION source restrictions
    CONSTRAINT chk_source_group_position CHECK (
        (source_type = 'GROUP_POSITION' AND source_group_id IS NOT NULL AND source_role IN ('WINNER', 'RUNNER_UP', 'GROUP_POSITION') AND 
         (source_role != 'GROUP_POSITION' OR (source_position IS NOT NULL AND source_position >= 1)))
        OR (source_type != 'GROUP_POSITION' OR source_type IS NULL)
    ),

    -- Check Matrix 6: POOL_RANK source restrictions
    CONSTRAINT chk_source_pool_rank CHECK (
        (source_type = 'POOL_RANK' AND source_pool_id IS NOT NULL AND source_role IS NULL AND source_rank IS NOT NULL AND source_rank >= 1)
        OR (source_type != 'POOL_RANK' OR source_type IS NULL)
    ),

    -- Check Matrix 7: Override provenance integrity
    CONSTRAINT chk_slot_override_provenance CHECK (
        (override_flag = true AND original_source_snapshot IS NOT NULL AND overridden_by_user_id IS NOT NULL AND overridden_at IS NOT NULL AND resolution_type = 'CONFIRMED_TEAM')
        OR (override_flag = false)
    )
);

-- -----------------------------------------------------------------------------
-- 2.15 Match (Operational Unit)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fixture_id UUID NOT NULL UNIQUE REFERENCES fixtures(id) ON DELETE CASCADE,
    venue_id UUID REFERENCES venues(id) ON DELETE SET NULL,
    status match_status NOT NULL DEFAULT 'SCHEDULED',
    assigned_scorer_id UUID REFERENCES users(id) ON DELETE SET NULL,
    actual_start_at TIMESTAMPTZ,
    actual_end_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_match_actual_times CHECK (
        actual_start_at IS NULL OR 
        actual_end_at IS NULL OR 
        actual_end_at >= actual_start_at
    )
);

-- -----------------------------------------------------------------------------
-- 2.16 Match_Result
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS match_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID NOT NULL UNIQUE REFERENCES matches(id) ON DELETE CASCADE,
    result_type match_result_type NOT NULL,
    winner_side winner_side NOT NULL,
    submitted_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    submitted_at TIMESTAMPTZ NOT NULL,
    locked_by UUID REFERENCES users(id) ON DELETE SET NULL,
    locked_at TIMESTAMPTZ,
    version INTEGER NOT NULL DEFAULT 1,
    correction_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_result_walkover_winner CHECK (
        (result_type = 'WALKOVER' AND winner_side IN ('A', 'B')) OR (result_type != 'WALKOVER')
    ),
    CONSTRAINT chk_result_correction_reason CHECK (
        (version > 1 AND correction_reason IS NOT NULL) OR (version <= 1)
    ),
    CONSTRAINT chk_result_lock_timestamp CHECK (
        locked_at IS NULL OR locked_at >= submitted_at
    )
);

-- -----------------------------------------------------------------------------
-- 2.17 Sport_Score_Detail
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sport_score_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID NOT NULL UNIQUE REFERENCES matches(id) ON DELETE CASCADE,
    sport_archetype sport_archetype NOT NULL,
    score_a INTEGER NOT NULL,
    score_b INTEGER NOT NULL,
    secondary_a INTEGER,
    secondary_b INTEGER,
    overs_a NUMERIC(5,1),
    overs_b NUMERIC(5,1),
    set_scores JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_score_non_negative CHECK (score_a >= 0 AND score_b >= 0),
    CONSTRAINT chk_score_archetype_contract CHECK (
        (sport_archetype = 'GOAL' AND secondary_a IS NULL AND secondary_b IS NULL AND overs_a IS NULL AND overs_b IS NULL AND set_scores IS NULL)
        OR
        (sport_archetype = 'OVER' AND overs_a IS NOT NULL AND overs_b IS NOT NULL AND overs_a > 0 AND overs_a <= 100 AND overs_b > 0 AND overs_b <= 100)
        OR
        (sport_archetype = 'SET' AND secondary_a IS NOT NULL AND secondary_b IS NOT NULL AND set_scores IS NOT NULL AND jsonb_typeof(set_scores) = 'array')
    )
);

-- -----------------------------------------------------------------------------
-- 2.18 Standing (Materialized Recompute-on-Write)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS standings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_id UUID NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    stage_id UUID NOT NULL REFERENCES tournament_stages(id) ON DELETE CASCADE,
    group_id UUID REFERENCES tournament_groups(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    played INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    draws INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    points INTEGER NOT NULL DEFAULT 0,
    metrics JSONB NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT chk_standing_position CHECK (position >= 1),
    CONSTRAINT chk_standing_counts CHECK (played >= 0 AND wins >= 0 AND draws >= 0 AND losses >= 0 AND points >= 0)
);

-- -----------------------------------------------------------------------------
-- 2.19 Medal_Award
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS medal_awards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_id UUID NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    medal_type medal_type NOT NULL,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    awarded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_medal_tournament_type UNIQUE (tournament_id, medal_type)
);

-- -----------------------------------------------------------------------------
-- 2.20 Protest
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS protests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    filed_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    filed_at TIMESTAMPTZ NOT NULL,
    reason_category protest_reason_category NOT NULL,
    description TEXT NOT NULL,
    status protest_status NOT NULL DEFAULT 'FILED',
    decided_by UUID REFERENCES users(id) ON DELETE SET NULL,
    decided_at TIMESTAMPTZ,
    jury_convener_name VARCHAR(120),
    jury_resolution_summary TEXT,
    action_taken VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_protest_decision_metadata CHECK (
        (status IN ('UPHELD', 'DISMISSED') AND 
         decided_by IS NOT NULL AND 
         decided_at IS NOT NULL AND 
         jury_convener_name IS NOT NULL AND 
         jury_resolution_summary IS NOT NULL AND 
         action_taken IS NOT NULL)
        OR (status NOT IN ('UPHELD', 'DISMISSED'))
    ),
    CONSTRAINT chk_protest_decision_time CHECK (
        decided_at IS NULL OR decided_at >= filed_at
    )
);

-- -----------------------------------------------------------------------------
-- 2.23 Audit_Log (Append-Only Generalized Audit)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(80) NOT NULL,
    subject_type audit_subject_type NOT NULL,
    subject_id UUID NOT NULL, -- Polymorphic reference (deliberately no hard FK)
    tournament_id UUID REFERENCES tournaments(id) ON DELETE SET NULL,
    before_data JSONB,
    after_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 2.24 Notification (One Row Per Recipient)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type notification_type NOT NULL,
    title VARCHAR(160) NOT NULL,
    message TEXT NOT NULL,
    reference_type notification_reference_type,
    reference_id UUID, -- Polymorphic reference (deliberately no hard FK)
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_notification_read_time CHECK (
        read_at IS NULL OR delivered_at IS NULL OR read_at >= delivered_at
    )
);
-- =============================================================================
-- 03_indexes.sql
-- Multi-Sport Tournament Fixture Generation Platform (v1.3 Frozen Spec)
-- Partial Unique Indexes and Performance Optimization Indexes
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Partial Unique Indexes (Domain Constraints from v1.3 Spec)
-- -----------------------------------------------------------------------------

-- 1. At most one Student Captain per Team (Section 2.8 E)
CREATE UNIQUE INDEX IF NOT EXISTS idx_team_representatives_captain 
ON team_representatives(team_id) 
WHERE designation = 'STUDENT_CAPTAIN';

-- 2. One slot per Pool Rank (Section 2.14 E - D1 final / v1.2)
-- Ensures that a specific rank qualifier from a pool fills at most one slot
CREATE UNIQUE INDEX IF NOT EXISTS idx_fixture_participants_pool_rank 
ON fixture_participants(source_pool_id, source_rank) 
WHERE source_type = 'POOL_RANK';

-- 3. Standings unique per team within scope (handles nullable group_id) (Section 2.18 E)
CREATE UNIQUE INDEX IF NOT EXISTS idx_standings_scope_team 
ON standings (
    stage_id, 
    COALESCE(group_id, '00000000-0000-0000-0000-000000000000'::uuid), 
    team_id
);

-- -----------------------------------------------------------------------------
-- Relational & Scheduling Query Optimization Indexes
-- -----------------------------------------------------------------------------

-- Tournament Hierarchy
CREATE INDEX IF NOT EXISTS idx_tournaments_event ON tournaments(championship_event_id);
CREATE INDEX IF NOT EXISTS idx_tournaments_host ON tournaments(host_college_id);
CREATE INDEX IF NOT EXISTS idx_stages_tournament ON tournament_stages(tournament_id);
CREATE INDEX IF NOT EXISTS idx_groups_stage ON tournament_groups(stage_id);

-- Teams & Rosters
CREATE INDEX IF NOT EXISTS idx_teams_tournament ON teams(tournament_id);
CREATE INDEX IF NOT EXISTS idx_teams_college ON teams(college_id);
CREATE INDEX IF NOT EXISTS idx_teams_group ON teams(group_id);
CREATE INDEX IF NOT EXISTS idx_teams_status ON teams(status);
CREATE INDEX IF NOT EXISTS idx_team_reps_user ON team_representatives(user_id);
CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_student_active ON players(student_id) WHERE status = 'ACTIVE';

-- Scheduling & Feasibility
CREATE INDEX IF NOT EXISTS idx_venues_event ON venues(championship_event_id);
CREATE INDEX IF NOT EXISTS idx_unavailability_venue_window ON unavailability_windows(venue_id, start_at, end_at);
CREATE INDEX IF NOT EXISTS idx_fixtures_stage ON fixtures(stage_id);
CREATE INDEX IF NOT EXISTS idx_fixtures_venue_time ON fixtures(venue_id, scheduled_start_at);
CREATE INDEX IF NOT EXISTS idx_fixtures_status ON fixtures(status);

-- Participants & Resolution
CREATE INDEX IF NOT EXISTS idx_fixture_participants_fixture ON fixture_participants(fixture_id);
CREATE INDEX IF NOT EXISTS idx_fixture_participants_team ON fixture_participants(team_id);
CREATE INDEX IF NOT EXISTS idx_fixture_participants_source_fixture ON fixture_participants(source_fixture_id);
CREATE INDEX IF NOT EXISTS idx_fixture_participants_source_group ON fixture_participants(source_group_id);
CREATE INDEX IF NOT EXISTS idx_fixture_participants_source_pool ON fixture_participants(source_pool_id);

-- Operational Matches & Scoring
CREATE INDEX IF NOT EXISTS idx_matches_venue ON matches(venue_id);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
CREATE INDEX IF NOT EXISTS idx_matches_scorer ON matches(assigned_scorer_id);

-- Protests & Disputes
CREATE INDEX IF NOT EXISTS idx_protests_match ON protests(match_id);
CREATE INDEX IF NOT EXISTS idx_protests_team ON protests(team_id);
CREATE INDEX IF NOT EXISTS idx_protests_status ON protests(status);

-- Audit & Notifications
CREATE INDEX IF NOT EXISTS idx_audit_logs_subject ON audit_logs(subject_type, subject_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_tournament ON audit_logs(tournament_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_recipient_unread ON notifications(recipient_id, read_at) WHERE read_at IS NULL;
-- =============================================================================
-- 04_business_logic_and_triggers.sql
-- Multi-Sport Tournament Fixture Generation Platform (v1.3 Frozen Spec)
-- Stored Procedures, Functions, and Invariant Enforcing Triggers
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Cross-Event Venue Consistency Guard (Rule 2.13 J7, 2.21 J5 - v1.3)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_enforce_cross_event_venue_consistency()
RETURNS TRIGGER AS $$
DECLARE
    v_fixture_event_id UUID;
    v_venue_event_id UUID;
BEGIN
    IF NEW.venue_id IS NOT NULL THEN
        -- Resolve the tournament's championship_event_id via the stage hierarchy
        SELECT t.championship_event_id INTO v_fixture_event_id
        FROM tournament_stages s
        JOIN tournaments t ON t.id = s.tournament_id
        WHERE s.id = NEW.stage_id;

        -- Resolve the venue's championship_event_id
        SELECT v.championship_event_id INTO v_venue_event_id
        FROM venues v
        WHERE v.id = NEW.venue_id;

        IF v_fixture_event_id IS DISTINCT FROM v_venue_event_id THEN
            RAISE EXCEPTION 'Cross-event venue mismatch: Fixture belongs to Championship_Event %, but Venue belongs to Championship_Event %',
                v_fixture_event_id, v_venue_event_id
                USING ERRCODE = 'check_violation';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_fixtures_venue_consistency ON fixtures;
CREATE TRIGGER trg_fixtures_venue_consistency
    BEFORE INSERT OR UPDATE OF venue_id, stage_id ON fixtures
    FOR EACH ROW
    EXECUTE FUNCTION trg_enforce_cross_event_venue_consistency();

-- -----------------------------------------------------------------------------
-- 2. Append-Only Immutability Guard for Audit Logs & Verification Records
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_prevent_append_only_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Table % is strictly append-only. UPDATE and DELETE operations are prohibited by system policy.',
        TG_TABLE_NAME
        USING ERRCODE = 'data_exception';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_logs_append_only ON audit_logs;
CREATE TRIGGER trg_audit_logs_append_only
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION trg_prevent_append_only_mutation();

DROP TRIGGER IF EXISTS trg_verification_records_append_only ON verification_records;
CREATE TRIGGER trg_verification_records_append_only
    BEFORE UPDATE OR DELETE ON verification_records
    FOR EACH ROW
    EXECUTE FUNCTION trg_prevent_append_only_mutation();

-- -----------------------------------------------------------------------------
-- 3. Synchronize Operational Venue of Record (Rule 2.15 J7, v1.2)
-- Dual-writes venue updates from Fixture to non-terminal Match
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_sync_fixture_match_venue()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.venue_id IS DISTINCT FROM OLD.venue_id THEN
        UPDATE matches
        SET venue_id = NEW.venue_id
        WHERE fixture_id = NEW.id
          AND status IN ('SCHEDULED', 'WARM_UP', 'POSTPONED', 'HELD_FOR_DISPUTE');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_fixtures_sync_match_venue ON fixtures;
CREATE TRIGGER trg_fixtures_sync_match_venue
    AFTER UPDATE OF venue_id ON fixtures
    FOR EACH ROW
    EXECUTE FUNCTION trg_sync_fixture_match_venue();

-- -----------------------------------------------------------------------------
-- 4. Participant Auto-Resolution Engine on Match Lock
-- Advances winners/losers into downstream slots (skipping overridden rows)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_resolve_match_advancement(p_match_id UUID)
RETURNS VOID AS $$
DECLARE
    v_fixture_id UUID;
    v_winner_side winner_side;
    v_team_a_id UUID;
    v_team_b_id UUID;
    v_winner_team_id UUID;
    v_loser_team_id UUID;
    v_target_slot RECORD;
BEGIN
    -- Fetch match and result context
    SELECT m.fixture_id, r.winner_side
    INTO v_fixture_id, v_winner_side
    FROM matches m
    JOIN match_results r ON r.match_id = m.id
    WHERE m.id = p_match_id AND m.status = 'LOCKED';

    IF NOT FOUND OR v_winner_side IS NULL OR v_winner_side = 'DRAW' THEN
        RETURN; -- No advancement on draws or unfinalized matches
    END IF;

    -- Fetch Team A and Team B from fixture participants
    SELECT team_id INTO v_team_a_id FROM fixture_participants WHERE fixture_id = v_fixture_id AND slot = 'A';
    SELECT team_id INTO v_team_b_id FROM fixture_participants WHERE fixture_id = v_fixture_id AND slot = 'B';

    IF v_winner_side = 'A' THEN
        v_winner_team_id := v_team_a_id;
        v_loser_team_id := v_team_b_id;
    ELSIF v_winner_side = 'B' THEN
        v_winner_team_id := v_team_b_id;
        v_loser_team_id := v_team_a_id;
    END IF;

    -- Update downstream participant slots (skipping override_flag = true)
    FOR v_target_slot IN
        SELECT id, fixture_id, slot, source_role
        FROM fixture_participants
        WHERE source_type = 'FIXTURE_RESULT'
          AND source_fixture_id = v_fixture_id
          AND override_flag = false
    LOOP
        IF v_target_slot.source_role = 'WINNER' AND v_winner_team_id IS NOT NULL THEN
            UPDATE fixture_participants
            SET resolution_type = 'CONFIRMED_TEAM',
                team_id = v_winner_team_id
            WHERE id = v_target_slot.id;

            -- Auto-create Match if both slots are now resolved and fixture is published
            PERFORM fn_try_spawn_match(v_target_slot.fixture_id);

        ELSIF v_target_slot.source_role = 'LOSER' AND v_loser_team_id IS NOT NULL THEN
            UPDATE fixture_participants
            SET resolution_type = 'CONFIRMED_TEAM',
                team_id = v_loser_team_id
            WHERE id = v_target_slot.id;

            PERFORM fn_try_spawn_match(v_target_slot.fixture_id);
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Helper to instantiate a Match when both slots are confirmed
CREATE OR REPLACE FUNCTION fn_try_spawn_match(p_fixture_id UUID)
RETURNS VOID AS $$
DECLARE
    v_fixture RECORD;
    v_slot_count INTEGER;
    v_confirmed_count INTEGER;
BEGIN
    SELECT * INTO v_fixture FROM fixtures WHERE id = p_fixture_id;
    IF v_fixture.status != 'PUBLISHED' THEN
        RETURN;
    END IF;

    SELECT COUNT(*), COUNT(CASE WHEN resolution_type IN ('CONFIRMED_TEAM', 'BYE') THEN 1 END)
    INTO v_slot_count, v_confirmed_count
    FROM fixture_participants
    WHERE fixture_id = p_fixture_id;

    -- If exactly 2 slots exist and both are confirmed/bye, ensure match row exists
    IF v_slot_count = 2 AND v_confirmed_count = 2 THEN
        INSERT INTO matches (fixture_id, venue_id, status)
        VALUES (v_fixture.id, v_fixture.venue_id, 'SCHEDULED')
        ON CONFLICT (fixture_id) DO NOTHING;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- 5. Standings Recomputation Engine (Rule 2.18, Frozen Decision #10)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_recompute_standings(p_stage_id UUID, p_group_id UUID DEFAULT NULL)
RETURNS VOID AS $$
DECLARE
    v_tournament_id UUID;
    v_sport sport_type;
    v_win_pts INTEGER := 3;
    v_draw_pts INTEGER := 1;
    v_loss_pts INTEGER := 0;
    v_scoring_cfg JSONB;
BEGIN
    -- Resolve tournament metadata
    SELECT t.id, t.sport, t.scoring_config
    INTO v_tournament_id, v_sport, v_scoring_cfg
    FROM tournament_stages s
    JOIN tournaments t ON t.id = s.tournament_id
    WHERE s.id = p_stage_id;

    IF NOT FOUND THEN
        RETURN;
    END IF;

    -- Configure sport points defaults if not overridden in json
    IF v_scoring_cfg ? 'win_points' THEN
        v_win_pts := (v_scoring_cfg->>'win_points')::INTEGER;
    ELSIF v_sport IN ('CRICKET', 'VOLLEYBALL', 'BASKETBALL', 'BADMINTON', 'KABADDI') THEN
        v_win_pts := 2;
    END IF;

    IF v_scoring_cfg ? 'draw_points' THEN
        v_draw_pts := (v_scoring_cfg->>'draw_points')::INTEGER;
    ELSIF v_sport IN ('CRICKET', 'VOLLEYBALL', 'BASKETBALL', 'BADMINTON') THEN
        v_draw_pts := 1; -- 1 pt for abandoned/tie where applicable
    END IF;

    -- Delete existing standings for this scope to allow clean atomic replacement
    DELETE FROM standings
    WHERE stage_id = p_stage_id
      AND ((p_group_id IS NULL AND group_id IS NULL) OR (group_id = p_group_id));

    -- Recompute aggregated statistics for all eligible teams in this group/stage
    WITH team_list AS (
        SELECT t.id AS team_id
        FROM teams t
        WHERE t.tournament_id = v_tournament_id
          AND ((p_group_id IS NULL AND t.group_id IS NULL) OR (t.group_id = p_group_id))
          AND t.status NOT IN ('DISQUALIFIED', 'WITHDRAWN', 'REJECTED')
    ),
    match_pairs AS (
        SELECT 
            m.id AS match_id,
            pa.team_id AS team_a,
            pb.team_id AS team_b,
            r.winner_side,
            r.result_type,
            sd.score_a,
            sd.score_b,
            sd.secondary_a,
            sd.secondary_b,
            sd.overs_a,
            sd.overs_b
        FROM matches m
        JOIN fixtures f ON f.id = m.fixture_id
        JOIN match_results r ON r.match_id = m.id
        JOIN sport_score_details sd ON sd.match_id = m.id
        JOIN fixture_participants pa ON pa.fixture_id = f.id AND pa.slot = 'A'
        JOIN fixture_participants pb ON pb.fixture_id = f.id AND pb.slot = 'B'
        WHERE f.stage_id = p_stage_id
          AND m.status = 'LOCKED'
          AND pa.team_id IS NOT NULL
          AND pb.team_id IS NOT NULL
    ),
    team_match_outcomes AS (
        -- Slot A perspective
        SELECT 
            mp.team_a AS team_id,
            1 AS played,
            CASE WHEN mp.winner_side = 'A' THEN 1 ELSE 0 END AS win,
            CASE WHEN mp.winner_side = 'DRAW' THEN 1 ELSE 0 END AS draw,
            CASE WHEN mp.winner_side = 'B' THEN 1 ELSE 0 END AS loss,
            mp.score_a AS scored,
            mp.score_b AS conceded,
            COALESCE(mp.secondary_a, 0) AS sec_for,
            COALESCE(mp.secondary_b, 0) AS sec_against,
            COALESCE(mp.overs_a, 0) AS ov_faced,
            COALESCE(mp.overs_b, 0) AS ov_bowled
        FROM match_pairs mp
        UNION ALL
        -- Slot B perspective
        SELECT 
            mp.team_b AS team_id,
            1 AS played,
            CASE WHEN mp.winner_side = 'B' THEN 1 ELSE 0 END AS win,
            CASE WHEN mp.winner_side = 'DRAW' THEN 1 ELSE 0 END AS draw,
            CASE WHEN mp.winner_side = 'A' THEN 1 ELSE 0 END AS loss,
            mp.score_b AS scored,
            mp.score_a AS conceded,
            COALESCE(mp.secondary_b, 0) AS sec_for,
            COALESCE(mp.secondary_a, 0) AS sec_against,
            COALESCE(mp.overs_b, 0) AS ov_faced,
            COALESCE(mp.overs_a, 0) AS ov_bowled
        FROM match_pairs mp
    ),
    aggregated_team_stats AS (
        SELECT 
            tl.team_id,
            COALESCE(SUM(tmo.played), 0) AS played,
            COALESCE(SUM(tmo.win), 0) AS wins,
            COALESCE(SUM(tmo.draw), 0) AS draws,
            COALESCE(SUM(tmo.loss), 0) AS losses,
            COALESCE(SUM(tmo.win), 0) * v_win_pts + COALESCE(SUM(tmo.draw), 0) * v_draw_pts AS points,
            COALESCE(SUM(tmo.scored), 0) AS total_scored,
            COALESCE(SUM(tmo.conceded), 0) AS total_conceded,
            COALESCE(SUM(tmo.scored), 0) - COALESCE(SUM(tmo.conceded), 0) AS diff,
            COALESCE(SUM(tmo.sec_for), 0) AS total_sec_for,
            COALESCE(SUM(tmo.sec_against), 0) AS total_sec_against
        FROM team_list tl
        LEFT JOIN team_match_outcomes tmo ON tmo.team_id = tl.team_id
        GROUP BY tl.team_id
    ),
    ranked_teams AS (
        SELECT 
            team_id,
            played,
            wins,
            draws,
            losses,
            points,
            diff,
            total_scored,
            total_conceded,
            total_sec_for,
            total_sec_against,
            ROW_NUMBER() OVER (ORDER BY points DESC, diff DESC, total_scored DESC) AS rank_pos
        FROM aggregated_team_stats
    )
    INSERT INTO standings (
        tournament_id,
        stage_id,
        group_id,
        team_id,
        position,
        played,
        wins,
        draws,
        losses,
        points,
        metrics,
        computed_at
    )
    SELECT 
        v_tournament_id,
        p_stage_id,
        p_group_id,
        rt.team_id,
        rt.rank_pos,
        rt.played,
        rt.wins,
        rt.draws,
        rt.losses,
        rt.points,
        jsonb_build_object(
            'gf', rt.total_scored,
            'ga', rt.total_conceded,
            'gd', rt.diff,
            'secondary_for', rt.total_sec_for,
            'secondary_against', rt.total_sec_against
        ),
        now()
    FROM ranked_teams rt;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- 6. Trigger on Match Result Locking -> Triggers Recompute & Advancement
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_on_match_result_locked()
RETURNS TRIGGER AS $$
DECLARE
    v_stage_id UUID;
    v_group_id UUID;
BEGIN
    IF NEW.locked_at IS NOT NULL AND (OLD.locked_at IS NULL OR NEW.version > OLD.version) THEN
        -- 1. Advance winners/losers
        PERFORM fn_resolve_match_advancement(NEW.match_id);

        -- 2. Identify stage and group for standings recompute
        SELECT f.stage_id, t.group_id
        INTO v_stage_id, v_group_id
        FROM matches m
        JOIN fixtures f ON f.id = m.fixture_id
        LEFT JOIN teams t ON t.id = (SELECT team_id FROM fixture_participants WHERE fixture_id = f.id LIMIT 1)
        WHERE m.id = NEW.match_id;

        IF v_stage_id IS NOT NULL THEN
            PERFORM fn_recompute_standings(v_stage_id, v_group_id);
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_match_results_locked_actions ON match_results;
CREATE TRIGGER trg_match_results_locked_actions
    AFTER INSERT OR UPDATE OF locked_at, version ON match_results
    FOR EACH ROW
    EXECUTE FUNCTION trg_on_match_result_locked();
-- =============================================================================
-- 05_row_level_security.sql
-- Multi-Sport Tournament Fixture Generation Platform (v1.3 Frozen Spec)
-- Supabase Row Level Security (RLS) Policies Across All 24 Tables
-- =============================================================================

-- Enable Row Level Security across all 24 tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE colleges ENABLE ROW LEVEL SECURITY;
ALTER TABLE championship_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE tournaments ENABLE ROW LEVEL SECURITY;
ALTER TABLE tournament_stages ENABLE ROW LEVEL SECURITY;
ALTER TABLE tournament_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_representatives ENABLE ROW LEVEL SECURITY;
ALTER TABLE players ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE qualification_pools ENABLE ROW LEVEL SECURITY;
ALTER TABLE qualification_pool_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE venues ENABLE ROW LEVEL SECURITY;
ALTER TABLE unavailability_windows ENABLE ROW LEVEL SECURITY;
ALTER TABLE fixtures ENABLE ROW LEVEL SECURITY;
ALTER TABLE fixture_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE match_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE sport_score_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE standings ENABLE ROW LEVEL SECURITY;
ALTER TABLE medal_awards ENABLE ROW LEVEL SECURITY;
ALTER TABLE protests ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- Helper Functions to evaluate Auth & Roles in Supabase RLS
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION auth_user_role()
RETURNS user_role AS $$
    SELECT role FROM users WHERE id = auth.uid() AND is_active = true;
$$ LANGUAGE sql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION is_super_admin()
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM users 
        WHERE id = auth.uid() 
          AND role = 'SUPER_ADMIN' 
          AND is_active = true
    );
$$ LANGUAGE sql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION is_team_rep_of(p_team_id UUID)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM team_representatives tr
        JOIN users u ON u.id = tr.user_id
        WHERE tr.team_id = p_team_id 
          AND tr.user_id = auth.uid()
          AND u.is_active = true
    );
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- -----------------------------------------------------------------------------
-- 1. Public Read-Only Policies (Viewers & Anonymous)
-- -----------------------------------------------------------------------------
CREATE POLICY "Public Read Colleges" ON colleges FOR SELECT USING (true);
CREATE POLICY "Public Read Events" ON championship_events FOR SELECT USING (true);
CREATE POLICY "Public Read Venues" ON venues FOR SELECT USING (true);

CREATE POLICY "Public Read Published Tournaments" ON tournaments 
    FOR SELECT USING (status != 'DRAFT' OR is_super_admin());

CREATE POLICY "Public Read Stages" ON tournament_stages 
    FOR SELECT USING (EXISTS (SELECT 1 FROM tournaments t WHERE t.id = tournament_id AND (t.status != 'DRAFT' OR is_super_admin())));

CREATE POLICY "Public Read Groups" ON tournament_groups FOR SELECT USING (true);

CREATE POLICY "Public Read Teams" ON teams 
    FOR SELECT USING (status NOT IN ('DRAFT', 'REJECTED') OR is_super_admin() OR is_team_rep_of(id));

CREATE POLICY "Public Read Players" ON players 
    FOR SELECT USING (status = 'ACTIVE' OR is_super_admin());

CREATE POLICY "Public Read Published Fixtures" ON fixtures 
    FOR SELECT USING (status = 'PUBLISHED' OR is_super_admin());

CREATE POLICY "Public Read Participants" ON fixture_participants FOR SELECT USING (true);
CREATE POLICY "Public Read Matches" ON matches FOR SELECT USING (true);
CREATE POLICY "Public Read Results" ON match_results FOR SELECT USING (true);
CREATE POLICY "Public Read Scores" ON sport_score_details FOR SELECT USING (true);
CREATE POLICY "Public Read Standings" ON standings FOR SELECT USING (true);
CREATE POLICY "Public Read Medals" ON medal_awards FOR SELECT USING (true);

-- -----------------------------------------------------------------------------
-- 2. Super Admin Full Access Policies
-- -----------------------------------------------------------------------------
CREATE POLICY "Admin Full Access Users" ON users FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Colleges" ON colleges FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Events" ON championship_events FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Tournaments" ON tournaments FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Stages" ON tournament_stages FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Groups" ON tournament_groups FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Teams" ON teams FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Team Reps" ON team_representatives FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Players" ON players FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Insert Verification" ON verification_records FOR INSERT WITH CHECK (is_super_admin());
CREATE POLICY "Admin Select Verification" ON verification_records FOR SELECT USING (is_super_admin());
CREATE POLICY "Admin Full Access Pools" ON qualification_pools FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Pool Members" ON qualification_pool_members FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Venues" ON venues FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Windows" ON unavailability_windows FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Fixtures" ON fixtures FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Participants" ON fixture_participants FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Matches" ON matches FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Results" ON match_results FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Scores" ON sport_score_details FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Standings" ON standings FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Medals" ON medal_awards FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Full Access Protests" ON protests FOR ALL USING (is_super_admin());
CREATE POLICY "Admin Insert Audit" ON audit_logs FOR INSERT WITH CHECK (true);
CREATE POLICY "Admin Select Audit" ON audit_logs FOR SELECT USING (is_super_admin());
CREATE POLICY "Admin Full Access Notifications" ON notifications FOR ALL USING (is_super_admin());

-- -----------------------------------------------------------------------------
-- 3. Scorer Policies (Field Mobile Console)
-- -----------------------------------------------------------------------------
CREATE POLICY "Scorers Update Assigned Match" ON matches
    FOR UPDATE USING (auth.uid() = assigned_scorer_id OR is_super_admin());

CREATE POLICY "Scorers Insert Match Result" ON match_results
    FOR INSERT WITH CHECK (
        submitted_by = auth.uid() AND 
        EXISTS (SELECT 1 FROM matches m WHERE m.id = match_id AND m.assigned_scorer_id = auth.uid())
    );

CREATE POLICY "Scorers Insert Score Details" ON sport_score_details
    FOR INSERT WITH CHECK (
        EXISTS (SELECT 1 FROM matches m WHERE m.id = match_id AND m.assigned_scorer_id = auth.uid())
    );

CREATE POLICY "Scorers Update Score Details" ON sport_score_details
    FOR UPDATE USING (
        EXISTS (SELECT 1 FROM matches m WHERE m.id = match_id AND m.assigned_scorer_id = auth.uid())
    );

-- -----------------------------------------------------------------------------
-- 4. Team Representative Policies (Captains & Managers)
-- -----------------------------------------------------------------------------
CREATE POLICY "Team Reps Manage Own Draft Team" ON teams
    FOR UPDATE USING (is_team_rep_of(id) AND status = 'DRAFT');

CREATE POLICY "Team Reps Manage Own Players" ON players
    FOR ALL USING (
        is_team_rep_of(team_id) AND 
        EXISTS (SELECT 1 FROM teams t WHERE t.id = team_id AND t.status IN ('DRAFT', 'REJECTED'))
    );

CREATE POLICY "Team Reps File Protest" ON protests
    FOR INSERT WITH CHECK (
        filed_by = auth.uid() AND 
        is_team_rep_of(team_id)
    );

CREATE POLICY "Team Reps View Own Protests" ON protests
    FOR SELECT USING (is_team_rep_of(team_id));

CREATE POLICY "Users Manage Own Notifications" ON notifications
    FOR ALL USING (recipient_id = auth.uid());
-- =============================================================================
-- 06_championship_leaderboard_view.sql
-- Multi-Sport Tournament Fixture Generation Platform (v1.3 Frozen Spec)
-- Derived View for Overall Championship Trophy Leaderboard (Section 2.3 J1 & 6)
-- =============================================================================

CREATE OR REPLACE VIEW v_championship_event_leaderboard AS
WITH event_medals AS (
    SELECT 
        ce.id AS championship_event_id,
        ce.name AS championship_event_name,
        ce.event_year,
        c.id AS college_id,
        c.name AS college_name,
        c.code AS college_code,
        COUNT(CASE WHEN ma.medal_type = 'GOLD' THEN 1 END) AS gold_count,
        COUNT(CASE WHEN ma.medal_type = 'SILVER' THEN 1 END) AS silver_count,
        COUNT(CASE WHEN ma.medal_type = 'BRONZE' THEN 1 END) AS bronze_count,
        ce.medal_points_gold,
        ce.medal_points_silver,
        ce.medal_points_bronze
    FROM championship_events ce
    JOIN tournaments t ON t.championship_event_id = ce.id
    JOIN medal_awards ma ON ma.tournament_id = t.id
    JOIN teams tm ON tm.id = ma.team_id
    JOIN colleges c ON c.id = tm.college_id
    GROUP BY ce.id, ce.name, ce.event_year, c.id, c.name, c.code, ce.medal_points_gold, ce.medal_points_silver, ce.medal_points_bronze
),
calculated_points AS (
    SELECT 
        championship_event_id,
        championship_event_name,
        event_year,
        college_id,
        college_name,
        college_code,
        gold_count,
        silver_count,
        bronze_count,
        (gold_count * medal_points_gold) + 
        (silver_count * medal_points_silver) + 
        (bronze_count * medal_points_bronze) AS total_points
    FROM event_medals
)
SELECT 
    championship_event_id,
    championship_event_name,
    event_year,
    college_id,
    college_name,
    college_code,
    gold_count,
    silver_count,
    bronze_count,
    total_points,
    DENSE_RANK() OVER (
        PARTITION BY championship_event_id 
        ORDER BY total_points DESC, gold_count DESC, silver_count DESC, bronze_count DESC
    ) AS rank
FROM calculated_points;

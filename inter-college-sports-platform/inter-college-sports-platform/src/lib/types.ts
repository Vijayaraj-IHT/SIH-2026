// =============================================================================
// TypeScript Domain Type Definitions (v1.3 Attribute-Level Frozen Spec)
// Multi-Sport Tournament Fixture Generation Platform
// =============================================================================

export type UserRole = 'SUPER_ADMIN' | 'SCORER' | 'TEAM_REPRESENTATIVE';
export type SportType = 'FOOTBALL' | 'CRICKET' | 'VOLLEYBALL' | 'BASKETBALL' | 'BADMINTON' | 'KABADDI' | 'TABLE_TENNIS' | 'TENNIS' | 'OTHER';
export type TournamentCategory = 'MEN' | 'WOMEN' | 'MIXED';
export type TournamentFormat = 'ROUND_ROBIN' | 'SINGLE_ELIMINATION' | 'GROUP_KNOCKOUT' | 'DOUBLE_ELIMINATION' | 'CUSTOM';
export type TournamentStatus = 'DRAFT' | 'PUBLISHED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
export type StageType = 'GROUP' | 'KNOCKOUT' | 'PLACEMENT' | 'OTHER';
export type StageStatus = 'DRAFT' | 'ACTIVE' | 'COMPLETED' | 'CANCELLED';
export type RegistrationRoute = 'ADVANCE' | 'SPOT';
export type TeamStatus = 'DRAFT' | 'PENDING' | 'VERIFIED' | 'PROVISIONAL_APPROVAL' | 'VERIFICATION_OVERDUE' | 'ACTIVE' | 'ELIMINATED' | 'CHAMPION' | 'DISQUALIFIED' | 'REJECTED' | 'WITHDRAWN';
export type RepresentativeDesignation = 'STUDENT_CAPTAIN' | 'FACULTY_MANAGER';
export type PlayerStatus = 'ACTIVE' | 'REMOVED';
export type VerificationType = 'DOCUMENT_CHECK' | 'IDENTITY_CHECK' | 'ROSTER_CHECK' | 'FULL_VERIFICATION';
export type VerificationOutcome = 'SUCCESS' | 'FAILED';
export type FixtureStatus = 'DRAFT' | 'PUBLISHED' | 'CANCELLED';
export type ParticipantSlot = 'A' | 'B';
export type SlotResolutionType = 'CONFIRMED_TEAM' | 'ADVANCEMENT_PENDING' | 'BYE';
export type ParticipantSourceType = 'FIXTURE_RESULT' | 'GROUP_POSITION' | 'POOL_RANK';
export type ParticipantSourceRole = 'WINNER' | 'RUNNER_UP' | 'LOSER' | 'GROUP_POSITION';
export type MatchStatus = 'SCHEDULED' | 'WARM_UP' | 'IN_PROGRESS' | 'STALLED' | 'PENDING_AUDIT' | 'UNDER_DISPUTE' | 'HELD_FOR_DISPUTE' | 'POSTPONED' | 'LOCKED' | 'ABANDONED' | 'CANCELLED';
export type MatchResultType = 'NORMAL' | 'WALKOVER';
export type WinnerSide = 'A' | 'B' | 'DRAW';
export type SportArchetype = 'GOAL' | 'OVER' | 'SET';
export type MedalType = 'GOLD' | 'SILVER' | 'BRONZE';
export type ProtestStatus = 'FILED' | 'UNDER_REVIEW' | 'UPHELD' | 'DISMISSED';
export type ProtestReasonCategory = 'ELIGIBILITY' | 'SCORING_ERROR' | 'CONDUCT' | 'OFFICIATING' | 'OTHER';
export type UnavailabilityReason = 'MAINTENANCE' | 'WEATHER' | 'OTHER_EVENT' | 'SECURITY' | 'OTHER';
export type AuditSubjectType = 'CHAMPIONSHIP_EVENT' | 'TOURNAMENT' | 'TOURNAMENT_STAGE' | 'TOURNAMENT_GROUP' | 'TEAM' | 'TEAM_REPRESENTATIVE' | 'PLAYER' | 'VERIFICATION_RECORD' | 'QUALIFICATION_POOL' | 'QUALIFICATION_POOL_MEMBER' | 'FIXTURE' | 'FIXTURE_PARTICIPANT' | 'MATCH' | 'MATCH_RESULT' | 'SPORT_SCORE_DETAIL' | 'PROTEST' | 'STANDING' | 'MEDAL_AWARD' | 'VENUE' | 'UNAVAILABILITY_WINDOW' | 'USER' | 'COLLEGE' | 'NOTIFICATION';
export type NotificationType = 'FIXTURE_SCHEDULED' | 'FIXTURE_RESCHEDULED' | 'RESULT_PUBLISHED' | 'PROTEST_FILED' | 'PROTEST_DECIDED' | 'VERIFICATION_DUE' | 'TEAM_VERIFIED' | 'TEAM_REJECTED' | 'TOURNAMENT_PUBLISHED' | 'GENERAL';

export interface User {
  id: string;
  full_name: string;
  email: string;
  phone?: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface College {
  id: string;
  name: string;
  code: string;
  email?: string;
  phone?: string;
  address?: string;
  created_at: string;
}

export interface ChampionshipEvent {
  id: string;
  name: string;
  event_year: number;
  start_date: string;
  end_date: string;
  description?: string;
  medal_points_gold: number;
  medal_points_silver: number;
  medal_points_bronze: number;
  created_at: string;
}

export interface Tournament {
  id: string;
  championship_event_id: string;
  name: string;
  sport: SportType;
  category: TournamentCategory;
  host_college_id: string;
  format: TournamentFormat;
  format_config?: Record<string, any>;
  tie_breaker_config?: Record<string, any>;
  scoring_config?: Record<string, any>;
  scheduling_constraints?: Record<string, any>;
  match_duration_minutes: number;
  reporting_lead_minutes?: number;
  status: TournamentStatus;
  registration_open_at?: string;
  registration_close_at?: string;
  planned_start_date?: string;
  planned_end_date?: string;
  published_at?: string;
  created_at: string;
  // Joins
  host_college?: College;
  championship_event?: ChampionshipEvent;
}

export interface TournamentStage {
  id: string;
  tournament_id: string;
  name: string;
  stage_type: StageType;
  sequence_order: number;
  description?: string;
  status: StageStatus;
  created_at: string;
  // Joins
  groups?: TournamentGroup[];
  fixtures?: Fixture[];
}

export interface TournamentGroup {
  id: string;
  stage_id: string;
  name: string;
  created_at: string;
  teams?: Team[];
}

export interface Team {
  id: string;
  tournament_id: string;
  college_id: string;
  team_name?: string;
  group_id?: string;
  seed_number?: number;
  registration_route: RegistrationRoute;
  status: TeamStatus;
  submitted_at?: string;
  created_at: string;
  // Joins
  college?: College;
  players?: Player[];
  representatives?: TeamRepresentative[];
}

export interface TeamRepresentative {
  id: string;
  team_id: string;
  user_id: string;
  designation: RepresentativeDesignation;
  created_at: string;
  user?: User;
}

export interface Player {
  id: string;
  team_id: string;
  student_id: string;
  full_name: string;
  year_of_study?: number;
  jersey_number?: number;
  position?: string;
  status: PlayerStatus;
  created_at: string;
}

export interface Venue {
  id: string;
  championship_event_id: string;
  name: string;
  area?: string;
  compatible_sports: SportType[];
  daily_open_time?: string;
  daily_close_time?: string;
  notes?: string;
  created_at: string;
}

export interface Fixture {
  id: string;
  stage_id: string;
  intra_stage_order: number;
  display_label?: string;
  scheduled_start_at?: string;
  venue_id?: string;
  status: FixtureStatus;
  published_at?: string;
  notes?: string;
  created_at: string;
  // Joins
  venue?: Venue;
  stage?: TournamentStage;
  participants?: FixtureParticipant[];
  match?: Match;
}

export interface FixtureParticipant {
  id: string;
  fixture_id: string;
  slot: ParticipantSlot;
  resolution_type: SlotResolutionType;
  team_id?: string;
  source_type?: ParticipantSourceType;
  source_fixture_id?: string;
  source_group_id?: string;
  source_pool_id?: string;
  source_role?: ParticipantSourceRole;
  source_position?: number;
  source_rank?: number;
  override_flag: boolean;
  original_source_snapshot?: Record<string, any>;
  overridden_by_user_id?: string;
  overridden_at?: string;
  override_reason?: string;
  created_at: string;
  // Joins
  team?: Team;
}

export interface Match {
  id: string;
  fixture_id: string;
  venue_id?: string;
  status: MatchStatus;
  assigned_scorer_id?: string;
  actual_start_at?: string;
  actual_end_at?: string;
  notes?: string;
  created_at: string;
  // Joins
  fixture?: Fixture;
  venue?: Venue;
  scorer?: User;
  result?: MatchResult;
  score_detail?: SportScoreDetail;
}

export interface MatchResult {
  id: string;
  match_id: string;
  result_type: MatchResultType;
  winner_side: WinnerSide;
  submitted_by: string;
  submitted_at: string;
  locked_by?: string;
  locked_at?: string;
  version: number;
  correction_reason?: string;
  created_at: string;
}

export interface SportScoreDetail {
  id: string;
  match_id: string;
  sport_archetype: SportArchetype;
  score_a: number;
  score_b: number;
  secondary_a?: number;
  secondary_b?: number;
  overs_a?: number;
  overs_b?: number;
  set_scores?: number[][];
  created_at: string;
}

export interface Standing {
  id: string;
  tournament_id: string;
  stage_id: string;
  group_id?: string;
  team_id: string;
  position: number;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  points: number;
  metrics: {
    gf?: number;
    ga?: number;
    gd?: number;
    runs?: number;
    wickets?: number;
    nrr?: number;
    sets_won?: number;
    sets_lost?: number;
    set_diff?: number;
    points_for?: number;
    points_against?: number;
  };
  computed_at: string;
  team?: Team;
}

export interface MedalAward {
  id: string;
  tournament_id: string;
  medal_type: MedalType;
  team_id: string;
  awarded_at: string;
  created_at: string;
  team?: Team;
}

export interface Protest {
  id: string;
  match_id: string;
  team_id: string;
  filed_by: string;
  filed_at: string;
  reason_category: ProtestReasonCategory;
  description: string;
  status: ProtestStatus;
  decided_by?: string;
  decided_at?: string;
  jury_convener_name?: string;
  jury_resolution_summary?: string;
  action_taken?: string;
  created_at: string;
  match?: Match;
  team?: Team;
}

export interface AuditLog {
  id: string;
  actor_id?: string;
  action: string;
  subject_type: AuditSubjectType;
  subject_id: string;
  tournament_id?: string;
  before_data?: Record<string, any>;
  after_data?: Record<string, any>;
  created_at: string;
  actor?: User;
}

export interface ChampionshipLeaderboardRow {
  championship_event_id: string;
  championship_event_name: string;
  event_year: number;
  college_id: string;
  college_name: string;
  college_code: string;
  gold_count: number;
  silver_count: number;
  bronze_count: number;
  total_points: number;
  rank: number;
}

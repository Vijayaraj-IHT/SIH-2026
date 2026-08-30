-- =============================================================================
-- 07_seed_data.sql
-- Multi-Sport Tournament Fixture Generation Platform (v1.3 Frozen Spec)
-- Realistic Sample Dataset for Inter-Collegiate Meet Validation
-- =============================================================================

DO $$
DECLARE
    -- User IDs
    v_admin_id UUID := '11111111-1111-1111-1111-111111111111';
    v_scorer_id UUID := '22222222-2222-2222-2222-222222222222';
    v_captain_gct_id UUID := '33333333-3333-3333-3333-333333333333';
    v_manager_psg_id UUID := '44444444-4444-4444-4444-444444444444';

    -- College IDs
    v_gct_id UUID := 'a1111111-aaaa-aaaa-aaaa-aaaaaaaaaaaa';
    v_psg_id UUID := 'a2222222-aaaa-aaaa-aaaa-aaaaaaaaaaaa';
    v_cit_id UUID := 'a3333333-aaaa-aaaa-aaaa-aaaaaaaaaaaa';
    v_tce_id UUID := 'a4444444-aaaa-aaaa-aaaa-aaaaaaaaaaaa';

    -- Event ID
    v_event_id UUID := 'e1111111-eeee-eeee-eeee-eeeeeeeeeeee';

    -- Venue IDs
    v_venue_pitch1 UUID := 'v1111111-vvvv-vvvv-vvvv-vvvvvvvvvvvv';
    v_venue_court1 UUID := 'v2222222-vvvv-vvvv-vvvv-vvvvvvvvvvvv';

    -- Tournament IDs
    v_tourn_fb_id UUID := 't1111111-tttt-tttt-tttt-tttttttttttt';
    v_tourn_vb_id UUID := 't2222222-tttt-tttt-tttt-tttttttttttt';

    -- Stage IDs
    v_stage_fb_final UUID := 's1111111-ssss-ssss-ssss-ssssssssssss';
    v_stage_vb_group UUID := 's2222222-ssss-ssss-ssss-ssssssssssss';

    -- Group ID
    v_group_vb_a UUID := 'g1111111-gggg-gggg-gggg-gggggggggggg';

    -- Team IDs (Football)
    v_team_fb_gct UUID := 'f1111111-ffff-ffff-ffff-ffffffffffff';
    v_team_fb_cit UUID := 'f2222222-ffff-ffff-ffff-ffffffffffff';

    -- Team IDs (Volleyball)
    v_team_vb_gct UUID := 'f3333333-ffff-ffff-ffff-ffffffffffff';
    v_team_vb_psg UUID := 'f4444444-ffff-ffff-ffff-ffffffffffff';

    -- Fixture & Match IDs
    v_fix_fb_final UUID := 'x1111111-xxxx-xxxx-xxxx-xxxxxxxxxxxx';
    v_match_fb_final UUID := 'm1111111-mmmm-mmmm-mmmm-mmmmmmmmmmmm';
BEGIN
    -- 1. Insert Users
    INSERT INTO users (id, full_name, email, phone, role, is_active)
    VALUES 
        (v_admin_id, 'Dr. R. Ramanathan', 'admin.sports@gct.ac.in', '+919876543210', 'SUPER_ADMIN', true),
        (v_scorer_id, 'K. Vignesh', 'vignesh.scorer@gmail.com', '+919876543211', 'SCORER', true),
        (v_captain_gct_id, 'M. Suresh', 'suresh.captain@gct.ac.in', '+919876543212', 'TEAM_REPRESENTATIVE', true),
        (v_manager_psg_id, 'Prof. S. Balaji', 'balaji.manager@psgtech.ac.in', '+919876543213', 'TEAM_REPRESENTATIVE', true)
    ON CONFLICT (id) DO NOTHING;

    -- 2. Insert Colleges
    INSERT INTO colleges (id, name, code, email, city)
    VALUES 
        (v_gct_id, 'Government College of Technology', 'GCT', 'sports@gct.ac.in', 'Coimbatore'),
        (v_psg_id, 'PSG College of Technology', 'PSG', 'sports@psgtech.ac.in', 'Coimbatore'),
        (v_cit_id, 'Coimbatore Institute of Technology', 'CIT', 'sports@cit.edu.in', 'Coimbatore'),
        (v_tce_id, 'Thiagarajar College of Engineering', 'TCE', 'sports@tce.edu', 'Madurai')
    ON CONFLICT (id) DO NOTHING;

    -- 3. Insert Championship Event
    INSERT INTO championship_events (id, name, event_year, start_date, end_date, description, medal_points_gold, medal_points_silver, medal_points_bronze)
    VALUES (v_event_id, 'State Inter-Collegiate Trophy 2026', 2026, '2026-09-10', '2026-09-15', 'Annual Inter-College Sports Championship', 5, 3, 1)
    ON CONFLICT (id) DO NOTHING;

    -- 4. Insert Venues (Scoped to Event)
    INSERT INTO venues (id, championship_event_id, name, area, compatible_sports, daily_open_time, daily_close_time)
    VALUES 
        (v_venue_pitch1, v_event_id, 'Main Ground (Pitch 1)', 'North Campus', '["FOOTBALL", "CRICKET"]'::jsonb, '07:00', '19:00'),
        (v_venue_court1, v_event_id, 'Indoor Stadium (Court 1)', 'Sports Complex', '["VOLLEYBALL", "BASKETBALL", "BADMINTON"]'::jsonb, '08:00', '20:00')
    ON CONFLICT (id) DO NOTHING;

    -- 5. Insert Tournaments (Football & Volleyball)
    INSERT INTO tournaments (id, championship_event_id, name, sport, category, host_college_id, format, match_duration_minutes, status, published_at)
    VALUES 
        (v_tourn_fb_id, v_event_id, 'Men''s Football Cup', 'FOOTBALL', 'MEN', v_gct_id, 'SINGLE_ELIMINATION', 90, 'IN_PROGRESS', now()),
        (v_tourn_vb_id, v_event_id, 'Men''s Volleyball League', 'VOLLEYBALL', 'MEN', v_gct_id, 'GROUP_KNOCKOUT', 60, 'PUBLISHED', now())
    ON CONFLICT (id) DO NOTHING;

    -- 6. Insert Stages & Groups
    INSERT INTO tournament_stages (id, tournament_id, name, stage_type, sequence_order, status)
    VALUES 
        (v_stage_fb_final, v_tourn_fb_id, 'Final Stage', 'KNOCKOUT', 1, 'ACTIVE'),
        (v_stage_vb_group, v_tourn_vb_id, 'Pool Stage', 'GROUP', 1, 'ACTIVE')
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO tournament_groups (id, stage_id, name)
    VALUES (v_group_vb_a, v_stage_vb_group, 'Pool A')
    ON CONFLICT (id) DO NOTHING;

    -- 7. Insert Teams
    INSERT INTO teams (id, tournament_id, college_id, team_name, status, registration_route)
    VALUES 
        (v_team_fb_gct, v_tourn_fb_id, v_gct_id, 'GCT Football Men', 'ACTIVE', 'ADVANCE'),
        (v_team_fb_cit, v_tourn_fb_id, v_cit_id, 'CIT Football Men', 'ACTIVE', 'ADVANCE'),
        (v_team_vb_gct, v_tourn_vb_id, v_gct_id, 'GCT Volleyball Men', 'ACTIVE', 'ADVANCE'),
        (v_team_vb_psg, v_tourn_vb_id, v_psg_id, 'PSG Volleyball Men', 'ACTIVE', 'ADVANCE')
    ON CONFLICT (id) DO NOTHING;

    -- Team Representatives
    INSERT INTO team_representatives (team_id, user_id, designation)
    VALUES 
        (v_team_fb_gct, v_captain_gct_id, 'STUDENT_CAPTAIN'),
        (v_team_vb_psg, v_manager_psg_id, 'FACULTY_MANAGER')
    ON CONFLICT (id) DO NOTHING;

    -- 8. Insert Players
    INSERT INTO players (team_id, student_id, full_name, year_of_study, jersey_number, position)
    VALUES 
        (v_team_fb_gct, '22GCT101', 'M. Suresh', 4, 10, 'Forward'),
        (v_team_fb_gct, '22GCT102', 'K. Praveen', 3, 1, 'Goalkeeper'),
        (v_team_fb_cit, '22CIT201', 'R. Arun', 4, 7, 'Midfielder')
    ON CONFLICT (id) DO NOTHING;

    -- 9. Insert Football Final Fixture & Participants
    INSERT INTO fixtures (id, stage_id, intra_stage_order, display_label, scheduled_start_at, venue_id, status, published_at)
    VALUES (v_fix_fb_final, v_stage_fb_final, 1, 'FINAL', now() - INTERVAL '2 hours', v_venue_pitch1, 'PUBLISHED', now() - INTERVAL '1 day')
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO fixture_participants (fixture_id, slot, resolution_type, team_id)
    VALUES 
        (v_fix_fb_final, 'A', 'CONFIRMED_TEAM', v_team_fb_gct),
        (v_fix_fb_final, 'B', 'CONFIRMED_TEAM', v_team_fb_cit)
    ON CONFLICT (id) DO NOTHING;

    -- 10. Operational Match, Result, and Score
    INSERT INTO matches (id, fixture_id, venue_id, status, assigned_scorer_id, actual_start_at, actual_end_at)
    VALUES (v_match_fb_final, v_fix_fb_final, v_venue_pitch1, 'LOCKED', v_scorer_id, now() - INTERVAL '2 hours', now() - INTERVAL '30 minutes')
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO match_results (match_id, result_type, winner_side, submitted_by, submitted_at, locked_by, locked_at)
    VALUES (v_match_fb_final, 'NORMAL', 'A', v_scorer_id, now() - INTERVAL '30 minutes', v_admin_id, now() - INTERVAL '20 minutes')
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO sport_score_details (match_id, sport_archetype, score_a, score_b)
    VALUES (v_match_fb_final, 'GOAL', 2, 1)
    ON CONFLICT (id) DO NOTHING;

    -- 11. Award Medals
    INSERT INTO medal_awards (tournament_id, medal_type, team_id, awarded_at)
    VALUES 
        (v_tourn_fb_id, 'GOLD', v_team_fb_gct, now() - INTERVAL '15 minutes'),
        (v_tourn_fb_id, 'SILVER', v_team_fb_cit, now() - INTERVAL '15 minutes')
    ON CONFLICT (id) DO NOTHING;

    -- 12. Audit Log Entry
    INSERT INTO audit_logs (actor_id, action, subject_type, subject_id, tournament_id, before_data, after_data)
    VALUES (v_admin_id, 'result.locked', 'MATCH_RESULT', v_match_fb_final, v_tourn_fb_id, '{"status": "PENDING_AUDIT"}'::jsonb, '{"status": "LOCKED", "winner_side": "A"}'::jsonb);

END $$;

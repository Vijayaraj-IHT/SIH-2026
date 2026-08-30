import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { Match, SportScoreDetail } from '@/lib/types';

export function useLiveMatch(initialMatch: Match) {
  const [match, setMatch] = useState<Match>(initialMatch);
  const [score, setScore] = useState<SportScoreDetail | undefined>(initialMatch.score_detail);

  useEffect(() => {
    if (!initialMatch?.id) return;

    // Listen for real-time match status updates
    const matchChannel = supabase
      .channel(`match-status-${initialMatch.id}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'matches',
          filter: `id=eq.${initialMatch.id}`,
        },
        (payload) => {
          setMatch((prev) => ({ ...prev, ...payload.new }));
        }
      )
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'sport_score_details',
          filter: `match_id=eq.${initialMatch.id}`,
        },
        (payload) => {
          setScore(payload.new as SportScoreDetail);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(matchChannel);
    };
  }, [initialMatch?.id]);

  return { match, score };
}

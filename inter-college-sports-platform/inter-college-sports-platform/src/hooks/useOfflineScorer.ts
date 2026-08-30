import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabaseClient';

export interface ScoreAction {
  id: string;
  matchId: string;
  actionType: 'SCORE_INCREMENT' | 'SET_WON' | 'TIMEOUT' | 'EXCEPTION';
  payload: any;
  timestamp: string;
  synced: boolean;
}

export function useOfflineScorer(matchId: string) {
  const [queue, setQueue] = useState<ScoreAction[]>([]);
  const [isOnline, setIsOnline] = useState(typeof window !== 'undefined' ? navigator.onLine : true);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Load queued actions from localStorage
    const saved = localStorage.getItem(`score_queue_${matchId}`);
    if (saved) {
      try {
        setQueue(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to parse score queue', e);
      }
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [matchId]);

  // Sync queued items when coming online
  useEffect(() => {
    if (isOnline && queue.some((item) => !item.synced)) {
      syncQueue();
    }
  }, [isOnline, queue]);

  const recordAction = async (actionType: ScoreAction['actionType'], payload: any) => {
    const action: ScoreAction = {
      id: crypto.randomUUID(),
      matchId,
      actionType,
      payload,
      timestamp: new Date().toISOString(),
      synced: false,
    };

    const newQueue = [...queue, action];
    setQueue(newQueue);
    localStorage.setItem(`score_queue_${matchId}`, JSON.stringify(newQueue));

    if (isOnline) {
      await syncItem(action);
    }
  };

  const syncItem = async (action: ScoreAction) => {
    try {
      if (action.actionType === 'SCORE_INCREMENT') {
        await supabase
          .from('sport_score_details')
          .update(action.payload)
          .eq('match_id', action.matchId);
      }

      setQueue((prev) =>
        prev.map((i) => (i.id === action.id ? { ...i, synced: true } : i))
      );
    } catch (err) {
      console.error('Failed to sync score item', err);
    }
  };

  const syncQueue = async () => {
    for (const item of queue.filter((i) => !i.synced)) {
      await syncItem(item);
    }
  };

  return { isOnline, pendingCount: queue.filter((i) => !i.synced).length, recordAction };
}

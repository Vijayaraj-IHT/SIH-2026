import React from 'react';
import Link from 'next/link';
import { Radio } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';

interface LiveScoreTickerProps {
  liveMatches: {
    id: string;
    sport: string;
    teamA: string;
    teamB: string;
    scoreA: string;
    scoreB: string;
    statusNote: string;
    venue: string;
  }[];
}

export const LiveScoreTicker: React.FC<LiveScoreTickerProps> = ({ liveMatches }) => {
  if (!liveMatches || liveMatches.length === 0) return null;

  return (
    <div className="bg-slate-900 border-b border-brand-900/50 py-2.5 px-4 overflow-x-auto scrollbar-none">
      <div className="max-w-7xl mx-auto flex items-center gap-6">
        <div className="flex items-center gap-2 flex-shrink-0 text-xs font-bold uppercase tracking-wider text-rose-400">
          <Radio className="w-4 h-4 animate-pulse text-rose-500" />
          <span>Live Now</span>
        </div>

        <div className="flex items-center gap-4 flex-nowrap overflow-x-auto">
          {liveMatches.map((m) => (
            <Link
              key={m.id}
              href={`/matches/${m.id}`}
              className="flex-shrink-0 bg-slate-800/90 hover:bg-slate-750 border border-slate-700/80 rounded-lg px-3 py-1.5 flex items-center gap-3 transition-colors text-xs text-white"
            >
              <Badge variant="warning">{m.sport}</Badge>
              <div className="font-semibold text-slate-200">
                {m.teamA} <span className="text-brand-400 font-bold">{m.scoreA}</span> - <span className="text-brand-400 font-bold">{m.scoreB}</span> {m.teamB}
              </div>
              <span className="text-[10px] text-slate-400">({m.statusNote})</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

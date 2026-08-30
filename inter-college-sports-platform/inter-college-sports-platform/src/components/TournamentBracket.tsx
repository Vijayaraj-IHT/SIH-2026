import React from 'react';
import { Badge } from '@/components/ui/Badge';

export interface BracketMatch {
  id: string;
  displayLabel: string;
  teamA: string;
  teamB: string;
  scoreA?: number | string;
  scoreB?: number | string;
  winnerSide?: 'A' | 'B' | 'DRAW';
  status: string;
  isBye?: boolean;
}

export interface BracketRound {
  name: string;
  matches: BracketMatch[];
}

interface TournamentBracketProps {
  rounds: BracketRound[];
}

export const TournamentBracket: React.FC<TournamentBracketProps> = ({ rounds }) => {
  if (!rounds || rounds.length === 0) return null;

  return (
    <div className="overflow-x-auto py-6 px-2 scrollbar-none">
      <div className="flex items-stretch gap-12 min-w-max">
        {rounds.map((round, roundIdx) => (
          <div key={round.name || roundIdx} className="flex flex-col justify-around w-64">
            <div className="text-center font-bold text-xs uppercase tracking-wider text-brand-400 bg-slate-800/80 py-2 rounded-lg mb-4 border border-slate-700">
              {round.name}
            </div>

            <div className="flex flex-col justify-around flex-grow gap-6">
              {round.matches.map((m) => (
                <div
                  key={m.id}
                  className="bg-slate-900 border border-slate-700/80 rounded-xl overflow-hidden shadow-md hover:border-brand-500/80 transition-all p-3"
                >
                  <div className="flex justify-between items-center text-[10px] text-slate-400 font-semibold mb-2">
                    <span>{m.displayLabel}</span>
                    <Badge variant={m.status === 'LOCKED' ? 'neutral' : m.status === 'IN_PROGRESS' ? 'danger' : 'info'}>
                      {m.status}
                    </Badge>
                  </div>

                  {/* Slot A */}
                  <div className={`flex justify-between items-center py-1.5 px-2 rounded font-medium text-xs ${
                    m.winnerSide === 'A' ? 'bg-emerald-900/40 text-emerald-300 font-bold' : 'text-slate-200'
                  }`}>
                    <span className="truncate">{m.teamA}</span>
                    <span className="font-mono ml-2">{m.scoreA ?? '-'}</span>
                  </div>

                  {/* Slot B */}
                  <div className={`flex justify-between items-center py-1.5 px-2 rounded font-medium text-xs mt-1 ${
                    m.winnerSide === 'B' ? 'bg-emerald-900/40 text-emerald-300 font-bold' : 'text-slate-200'
                  }`}>
                    <span className="truncate">{m.teamB}</span>
                    <span className="font-mono ml-2">{m.scoreB ?? '-'}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

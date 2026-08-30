'use client';

import React, { useState } from 'react';
import { Trophy, Calendar, MapPin, Layers, Award, Radio } from 'lucide-react';
import { TournamentBracket, BracketRound } from '@/components/TournamentBracket';
import { PointsTable } from '@/components/PointsTable';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

export default function TournamentDetailPage() {
  const [activeTab, setActiveTab] = useState<'BRACKET' | 'STANDINGS' | 'FIXTURES'>('BRACKET');

  const knockoutRounds: BracketRound[] = [
    {
      name: 'Quarter Finals',
      matches: [
        { id: 'm1', displayLabel: 'QF 1', teamA: 'GCT (Coimbatore)', teamB: 'TCE (Madurai)', scoreA: 3, scoreB: 1, winnerSide: 'A', status: 'LOCKED' },
        { id: 'm2', displayLabel: 'QF 2', teamA: 'CIT (Coimbatore)', teamB: 'ACC (Karaikudi)', scoreA: 2, scoreB: 0, winnerSide: 'A', status: 'LOCKED' },
        { id: 'm3', displayLabel: 'QF 3', teamA: 'PSG Tech', teamB: 'KCT (Coimbatore)', scoreA: 2, scoreB: 1, winnerSide: 'A', status: 'LOCKED' },
        { id: 'm4', displayLabel: 'QF 4', teamA: 'MIT (Chennai)', teamB: 'RIT (Chennai)', scoreA: 1, scoreB: 0, winnerSide: 'A', status: 'LOCKED' },
      ],
    },
    {
      name: 'Semi Finals',
      matches: [
        { id: 'm5', displayLabel: 'SF 1', teamA: 'GCT (Coimbatore)', teamB: 'CIT (Coimbatore)', scoreA: 2, scoreB: 1, winnerSide: 'A', status: 'LOCKED' },
        { id: 'm6', displayLabel: 'SF 2', teamA: 'PSG Tech', teamB: 'MIT (Chennai)', scoreA: 3, scoreB: 2, winnerSide: 'A', status: 'LOCKED' },
      ],
    },
    {
      name: 'Final',
      matches: [
        { id: 'm7', displayLabel: 'FINAL', teamA: 'GCT (Coimbatore)', teamB: 'PSG Tech', scoreA: 2, scoreB: 1, winnerSide: 'A', status: 'LOCKED' },
      ],
    },
  ];

  const sampleStandings = [
    {
      id: 'st1',
      tournament_id: 't1',
      stage_id: 's1',
      team_id: 'tm1',
      position: 1,
      played: 3,
      wins: 3,
      draws: 0,
      losses: 0,
      points: 9,
      metrics: { gf: 8, ga: 2, gd: 6 },
      computed_at: new Date().toISOString(),
      team: { team_name: 'GCT Football Men', college: { name: 'Government College of Technology' } } as any,
    },
    {
      id: 'st2',
      tournament_id: 't1',
      stage_id: 's1',
      team_id: 'tm2',
      position: 2,
      played: 3,
      wins: 2,
      draws: 0,
      losses: 1,
      points: 6,
      metrics: { gf: 5, ga: 3, gd: 2 },
      computed_at: new Date().toISOString(),
      team: { team_name: 'CIT Football Men', college: { name: 'Coimbatore Institute of Technology' } } as any,
    },
    {
      id: 'st3',
      tournament_id: 't1',
      stage_id: 's1',
      team_id: 'tm3',
      position: 3,
      played: 3,
      wins: 1,
      draws: 0,
      losses: 2,
      points: 3,
      metrics: { gf: 3, ga: 5, gd: -2 },
      computed_at: new Date().toISOString(),
      team: { team_name: 'TCE Football Men', college: { name: 'Thiagarajar College of Engineering' } } as any,
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Tournament Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 shadow-xl">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="info">FOOTBALL • MEN</Badge>
            <Badge variant="danger">IN_PROGRESS</Badge>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            Men&apos;s Football Cup 2026
          </h1>
          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 mt-2">
            <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> Main Ground (Pitch 1)</span>
            <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> Sep 10 - Sep 15, 2026</span>
            <span className="flex items-center gap-1"><Trophy className="w-3.5 h-3.5" /> Single Elimination</span>
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            variant={activeTab === 'BRACKET' ? 'primary' : 'outline'}
            onClick={() => setActiveTab('BRACKET')}
            className="flex items-center gap-1.5"
          >
            <Layers className="w-4 h-4" /> Knockout Tree
          </Button>
          <Button
            variant={activeTab === 'STANDINGS' ? 'primary' : 'outline'}
            onClick={() => setActiveTab('STANDINGS')}
            className="flex items-center gap-1.5"
          >
            <Trophy className="w-4 h-4" /> Points Table
          </Button>
        </div>
      </div>

      {/* Active Tab View */}
      {activeTab === 'BRACKET' && (
        <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-brand-400" /> Single Elimination Championship Tree
            </h2>
            <span className="text-xs text-slate-400">Auto-Resolved on Match Finalization</span>
          </div>
          <TournamentBracket rounds={knockoutRounds} />
        </div>
      )}

      {activeTab === 'STANDINGS' && (
        <div className="space-y-6">
          <PointsTable title="Pool A Standings" standings={sampleStandings as any} sport="FOOTBALL" />
        </div>
      )}
    </div>
  );
}

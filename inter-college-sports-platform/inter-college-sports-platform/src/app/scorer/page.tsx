'use client';

import React from 'react';
import Link from 'next/link';
import { Radio, Play, CheckCircle2, Clock } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

export default function ScorerDashboardPage() {
  const assignedMatches = [
    {
      id: 'm1111111-mmmm-mmmm-mmmm-mmmmmmmmmmmm',
      sport: 'FOOTBALL',
      category: 'MEN',
      teamA: 'GCT (Coimbatore)',
      teamB: 'CIT (Coimbatore)',
      venue: 'Main Ground (Pitch 1)',
      scheduledTime: '02:00 PM',
      status: 'IN_PROGRESS',
      scoreSummary: 'GCT 2 - 1 CIT (78\')',
    },
    {
      id: 'm2222222-mmmm-mmmm-mmmm-mmmmmmmmmmmm',
      sport: 'VOLLEYBALL',
      category: 'MEN',
      teamA: 'PSG Tech',
      teamB: 'TCE (Madurai)',
      venue: 'Indoor Stadium (Court 1)',
      scheduledTime: '03:30 PM',
      status: 'SCHEDULED',
      scoreSummary: 'Upcoming',
    },
  ];

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex justify-between items-center">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase tracking-wider mb-1">
            <Radio className="w-4 h-4 animate-pulse" /> Official Scorer Terminal
          </div>
          <h1 className="text-2xl font-extrabold text-white">
            Today&apos;s Assigned Matches
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Operator: K. Vignesh (Official Ground Scorer) • Ground Wi-Fi Online
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {assignedMatches.map((m) => (
          <div
            key={m.id}
            className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 hover:border-brand-500/50 transition-all"
          >
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="info">{m.sport}</Badge>
                <Badge variant={m.status === 'IN_PROGRESS' ? 'danger' : 'neutral'}>
                  {m.status}
                </Badge>
              </div>
              <h3 className="text-base font-bold text-white">
                {m.teamA} vs {m.teamB}
              </h3>
              <div className="text-xs text-slate-400 flex items-center gap-3 mt-1.5">
                <span>📍 {m.venue}</span>
                <span>⏰ {m.scheduledTime}</span>
              </div>
            </div>

            <Link href={`/scorer/live/${m.id}`}>
              <Button variant="primary" className="flex items-center gap-2 w-full sm:w-auto">
                <Play className="w-4 h-4" /> Open Scoring Console
              </Button>
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}

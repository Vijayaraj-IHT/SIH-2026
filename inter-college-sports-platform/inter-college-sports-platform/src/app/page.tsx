'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Trophy, Calendar, MapPin, ChevronRight, Activity, Award } from 'lucide-react';
import { LiveScoreTicker } from '@/components/LiveScoreTicker';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

export default function HomePage() {
  const [selectedSport, setSelectedSport] = useState<string>('ALL');

  const liveMatches = [
    {
      id: 'm1111111-mmmm-mmmm-mmmm-mmmmmmmmmmmm',
      sport: 'FOOTBALL',
      teamA: 'GCT',
      teamB: 'CIT',
      scoreA: '2',
      scoreB: '1',
      statusNote: "78'",
      venue: 'Main Ground (Pitch 1)',
    },
    {
      id: 'm2222222-mmmm-mmmm-mmmm-mmmmmmmmmmmm',
      sport: 'VOLLEYBALL',
      teamA: 'PSG',
      teamB: 'TCE',
      scoreA: '25, 14',
      scoreB: '22, 11',
      statusNote: 'Set 2 In Progress',
      venue: 'Indoor Stadium (Court 1)',
    },
  ];

  const tournaments = [
    {
      id: 't1111111-tttt-tttt-tttt-tttttttttttt',
      name: "Men's Football Cup",
      sport: 'FOOTBALL',
      category: 'MEN',
      format: 'SINGLE_ELIMINATION',
      teamsCount: 8,
      status: 'IN_PROGRESS',
      stage: 'Semi Finals',
      venue: 'Main Ground (Pitch 1)',
    },
    {
      id: 't2222222-tttt-tttt-tttt-tttttttttttt',
      name: "Men's Volleyball League",
      sport: 'VOLLEYBALL',
      category: 'MEN',
      format: 'GROUP_KNOCKOUT',
      teamsCount: 12,
      status: 'IN_PROGRESS',
      stage: 'Pool Stages (Pool A & B)',
      venue: 'Indoor Stadium (Court 1)',
    },
    {
      id: 't3333333-tttt-tttt-tttt-tttttttttttt',
      name: "Men's Cricket T20 Championship",
      sport: 'CRICKET',
      category: 'MEN',
      format: 'ROUND_ROBIN',
      teamsCount: 6,
      status: 'PUBLISHED',
      stage: 'Round 3 of 5',
      venue: 'Cricket Oval (North Pitch)',
    },
    {
      id: 't4444444-tttt-tttt-tttt-tttttttttttt',
      name: "Women's Badminton Singles",
      sport: 'BADMINTON',
      category: 'WOMEN',
      format: 'SINGLE_ELIMINATION',
      teamsCount: 16,
      status: 'PUBLISHED',
      stage: 'Quarter Finals',
      venue: 'Badminton Arena (Court A)',
    },
    {
      id: 't5555555-tttt-tttt-tttt-tttttttttttt',
      name: "Men's Basketball Trophy",
      sport: 'BASKETBALL',
      category: 'MEN',
      format: 'GROUP_KNOCKOUT',
      teamsCount: 8,
      status: 'PUBLISHED',
      stage: 'Group Stages',
      venue: 'Outdoor Hardcourt B',
    },
    {
      id: 't6666666-tttt-tttt-tttt-tttttttttttt',
      name: "Inter-College Kabaddi Meet",
      sport: 'KABADDI',
      category: 'MEN',
      format: 'SINGLE_ELIMINATION',
      teamsCount: 10,
      status: 'PUBLISHED',
      stage: 'Round of 16',
      venue: 'Kabaddi Mat 1',
    },
  ];

  const sportsList = ['ALL', 'FOOTBALL', 'VOLLEYBALL', 'CRICKET', 'BADMINTON', 'BASKETBALL', 'KABADDI'];

  const filteredTournaments = selectedSport === 'ALL'
    ? tournaments
    : tournaments.filter((t) => t.sport === selectedSport);

  return (
    <div className="space-y-8">
      {/* Live Marquee Ticker */}
      <LiveScoreTicker liveMatches={liveMatches} />

      {/* Hero Banner */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
        <div className="bg-gradient-to-r from-slate-900 via-slate-850 to-brand-950/80 border border-slate-800 rounded-2xl p-6 sm:p-10 shadow-2xl relative overflow-hidden">
          <div className="relative z-10 max-w-2xl">
            <Badge variant="success" className="mb-3">
              State Inter-Collegiate Meet 2026
            </Badge>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
              Live Fixtures, Instant Scoring & Championship Standings
            </h1>
            <p className="mt-3 text-slate-300 text-sm sm:text-base leading-relaxed">
              Official live tournament engine for university athletes, coaches, and sports directors. 
              Track group stages, knockout brackets, and the overall medal tally in real time.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/leaderboard">
                <Button variant="primary" className="flex items-center gap-2">
                  <Award className="w-4 h-4" /> View Overall Trophy
                </Button>
              </Link>
              <Link href="/captain/dashboard">
                <Button variant="outline" className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" /> Captain Check-In
                </Button>
              </Link>
            </div>
          </div>
          <div className="absolute right-0 bottom-0 opacity-10 pointer-events-none transform translate-x-12 translate-y-12">
            <Trophy className="w-96 h-96 text-brand-400" />
          </div>
        </div>
      </div>

      {/* Sport Category Filter Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
          {sportsList.map((sp) => (
            <button
              key={sp}
              onClick={() => setSelectedSport(sp)}
              className={`px-4 py-2 rounded-xl text-xs font-bold uppercase transition-all ${
                selectedSport === sp
                  ? 'bg-brand-600 text-white shadow-md'
                  : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
              }`}
            >
              {sp}
            </button>
          ))}
        </div>
      </div>

      {/* Tournaments Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-brand-400" /> Tournaments & Sports Brackets
          </h2>
          <span className="text-xs text-slate-400">{filteredTournaments.length} Sports Running</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTournaments.map((tourn) => (
            <div
              key={tourn.id}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg hover:border-brand-500/60 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex justify-between items-start mb-3">
                  <Badge variant={tourn.sport === 'FOOTBALL' ? 'info' : tourn.sport === 'CRICKET' ? 'warning' : 'success'}>
                    {tourn.sport} • {tourn.category}
                  </Badge>
                  <Badge variant={tourn.status === 'IN_PROGRESS' ? 'danger' : 'neutral'}>
                    {tourn.status}
                  </Badge>
                </div>

                <h3 className="text-lg font-bold text-white mb-2">{tourn.name}</h3>
                
                <div className="space-y-1.5 text-xs text-slate-400 mb-6">
                  <div className="flex items-center gap-1.5">
                    <Trophy className="w-3.5 h-3.5 text-brand-400" />
                    <span>Format: <strong className="text-slate-200">{tourn.format.replace('_', ' ')}</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>Active Stage: <strong className="text-slate-200">{tourn.stage}</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    <span>{tourn.venue}</span>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300">{tourn.teamsCount} Colleges</span>
                <Link
                  href={`/tournaments/${tourn.id}`}
                  className="inline-flex items-center text-xs font-bold text-brand-400 hover:text-brand-300 gap-1"
                >
                  View Brackets & Fixtures <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

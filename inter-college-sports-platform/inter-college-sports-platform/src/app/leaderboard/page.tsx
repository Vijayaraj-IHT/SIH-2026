'use client';

import React from 'react';
import { Award, Trophy, Medal } from 'lucide-react';
import { ChampionshipLeaderboardRow } from '@/lib/types';

export default function LeaderboardPage() {
  const leaderboardData: ChampionshipLeaderboardRow[] = [
    {
      championship_event_id: 'e111',
      championship_event_name: 'State Inter-Collegiate Trophy 2026',
      event_year: 2026,
      college_id: 'c1',
      college_name: 'Government College of Technology',
      college_code: 'GCT',
      gold_count: 3,
      silver_count: 1,
      bronze_count: 2,
      total_points: 20,
      rank: 1,
    },
    {
      championship_event_id: 'e111',
      championship_event_name: 'State Inter-Collegiate Trophy 2026',
      event_year: 2026,
      college_id: 'c2',
      college_name: 'PSG College of Technology',
      college_code: 'PSG',
      gold_count: 2,
      silver_count: 3,
      bronze_count: 1,
      total_points: 20,
      rank: 2,
    },
    {
      championship_event_id: 'e111',
      championship_event_name: 'State Inter-Collegiate Trophy 2026',
      event_year: 2026,
      college_id: 'c3',
      college_name: 'Coimbatore Institute of Technology',
      college_code: 'CIT',
      gold_count: 1,
      silver_count: 2,
      bronze_count: 3,
      total_points: 14,
      rank: 3,
    },
    {
      championship_event_id: 'e111',
      championship_event_name: 'State Inter-Collegiate Trophy 2026',
      event_year: 2026,
      college_id: 'c4',
      college_name: 'Thiagarajar College of Engineering',
      college_code: 'TCE',
      gold_count: 1,
      silver_count: 1,
      bronze_count: 1,
      total_points: 9,
      rank: 4,
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 shadow-xl">
        <div>
          <div className="flex items-center gap-2 text-brand-400 text-xs font-bold uppercase tracking-wider mb-2">
            <Award className="w-4 h-4" /> Official General Championship Tally
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            Overall Institutional Trophy Leaderboard
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-xl">
            Points aggregated dynamically across Men&apos;s, Women&apos;s, and Mixed tournaments. 
            Gold = 5 Pts, Silver = 3 Pts, Bronze = 1 Pt.
          </p>
        </div>

        <div className="flex items-center gap-4 bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
          <div>
            <div className="text-xl font-extrabold text-amber-400">5 Pts</div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Gold</div>
          </div>
          <div className="h-8 w-px bg-slate-800" />
          <div>
            <div className="text-xl font-extrabold text-slate-300">3 Pts</div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Silver</div>
          </div>
          <div className="h-8 w-px bg-slate-800" />
          <div>
            <div className="text-xl font-extrabold text-amber-700">1 Pt</div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Bronze</div>
          </div>
        </div>
      </div>

      {/* Podium Cards for Top 3 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {leaderboardData.slice(0, 3).map((col) => (
          <div
            key={col.college_id}
            className={`rounded-2xl p-6 border flex flex-col justify-between relative overflow-hidden shadow-lg ${
              col.rank === 1
                ? 'bg-gradient-to-b from-amber-950/40 to-slate-900 border-amber-500/50'
                : col.rank === 2
                ? 'bg-gradient-to-b from-slate-800/60 to-slate-900 border-slate-600/50'
                : 'bg-gradient-to-b from-amber-900/20 to-slate-900 border-amber-800/40'
            }`}
          >
            <div>
              <div className="flex justify-between items-center mb-4">
                <span className={`w-8 h-8 rounded-full flex items-center justify-center font-black text-sm ${
                  col.rank === 1 ? 'bg-amber-500 text-slate-950' : col.rank === 2 ? 'bg-slate-300 text-slate-950' : 'bg-amber-700 text-white'
                }`}>
                  #{col.rank}
                </span>
                <Trophy className={`w-6 h-6 ${col.rank === 1 ? 'text-amber-400' : col.rank === 2 ? 'text-slate-300' : 'text-amber-600'}`} />
              </div>
              <h3 className="text-lg font-bold text-white leading-snug">{col.college_name}</h3>
              <span className="text-xs font-semibold text-brand-400 block mt-1">({col.college_code})</span>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800 flex justify-between items-end">
              <div className="flex items-center gap-3 text-xs">
                <span className="text-amber-400 font-bold">🥇 {col.gold_count}</span>
                <span className="text-slate-300 font-bold">🥈 {col.silver_count}</span>
                <span className="text-amber-600 font-bold">🥉 {col.bronze_count}</span>
              </div>
              <div className="text-right">
                <span className="text-2xl font-black text-white">{col.total_points}</span>
                <span className="text-[10px] text-slate-400 uppercase block font-semibold">Total Pts</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Full Leaderboard Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
            <tr>
              <th className="px-6 py-4 font-bold">Rank</th>
              <th className="px-6 py-4 font-bold">College Institution</th>
              <th className="px-4 py-4 font-bold text-center">Code</th>
              <th className="px-4 py-4 font-bold text-center text-amber-400">Gold (5)</th>
              <th className="px-4 py-4 font-bold text-center text-slate-300">Silver (3)</th>
              <th className="px-4 py-4 font-bold text-center text-amber-600">Bronze (1)</th>
              <th className="px-6 py-4 font-black text-right text-white">Total Points</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {leaderboardData.map((row) => (
              <tr key={row.college_id} className="hover:bg-slate-850/50 transition-colors">
                <td className="px-6 py-4 font-extrabold text-white">
                  #{row.rank}
                </td>
                <td className="px-6 py-4 font-bold text-white">
                  {row.college_name}
                </td>
                <td className="px-4 py-4 text-center font-mono font-semibold text-slate-400">
                  {row.college_code}
                </td>
                <td className="px-4 py-4 text-center font-bold text-amber-400">
                  {row.gold_count}
                </td>
                <td className="px-4 py-4 text-center font-bold text-slate-300">
                  {row.silver_count}
                </td>
                <td className="px-4 py-4 text-center font-bold text-amber-600">
                  {row.bronze_count}
                </td>
                <td className="px-6 py-4 text-right font-black text-lg text-brand-400">
                  {row.total_points}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

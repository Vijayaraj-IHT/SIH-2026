import React from 'react';
import { Standing } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';

interface PointsTableProps {
  title?: string;
  standings: Standing[];
  sport: string;
}

export const PointsTable: React.FC<PointsTableProps> = ({ title = 'Group Standings', standings, sport }) => {
  const isCricket = sport === 'CRICKET';
  const isVolleyball = sport === 'VOLLEYBALL' || sport === 'BADMINTON';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
      <div className="px-5 py-3.5 border-b border-slate-800 bg-slate-850 flex items-center justify-between">
        <h3 className="font-bold text-sm text-white tracking-wide">{title}</h3>
        <span className="text-xs text-slate-400 font-medium">Top 2 Qualify for Knockouts</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-800 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-700">
            <tr>
              <th className="px-4 py-3 font-semibold">Pos</th>
              <th className="px-4 py-3 font-semibold">College / Team</th>
              <th className="px-3 py-3 font-semibold text-center">P</th>
              <th className="px-3 py-3 font-semibold text-center">W</th>
              <th className="px-3 py-3 font-semibold text-center">D</th>
              <th className="px-3 py-3 font-semibold text-center">L</th>
              {isCricket && (
                <>
                  <th className="px-3 py-3 font-semibold text-center">Runs</th>
                  <th className="px-3 py-3 font-semibold text-center">NRR</th>
                </>
              )}
              {isVolleyball && (
                <>
                  <th className="px-3 py-3 font-semibold text-center">Sets Diff</th>
                  <th className="px-3 py-3 font-semibold text-center">Pts Ratio</th>
                </>
              )}
              {!isCricket && !isVolleyball && (
                <>
                  <th className="px-3 py-3 font-semibold text-center">GF</th>
                  <th className="px-3 py-3 font-semibold text-center">GA</th>
                  <th className="px-3 py-3 font-semibold text-center">GD</th>
                </>
              )}
              <th className="px-4 py-3 font-bold text-center text-white bg-slate-850">PTS</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {standings.map((s, idx) => {
              const isQualifying = idx < 2;
              return (
                <tr
                  key={s.id || idx}
                  className={`hover:bg-slate-800/50 transition-colors ${
                    isQualifying ? 'bg-emerald-950/20' : ''
                  }`}
                >
                  <td className="px-4 py-3 font-bold">
                    <span className={`inline-flex w-5 h-5 items-center justify-center rounded-full text-xs ${
                      isQualifying ? 'bg-emerald-600 text-white' : 'text-slate-400'
                    }`}>
                      {s.position}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-semibold text-white flex items-center gap-2">
                    {s.team?.team_name || s.team?.college?.name || 'College Team'}
                    {isQualifying && <Badge variant="success" className="text-[9px] py-0 px-1.5">Q</Badge>}
                  </td>
                  <td className="px-3 py-3 text-center">{s.played}</td>
                  <td className="px-3 py-3 text-center font-medium text-emerald-400">{s.wins}</td>
                  <td className="px-3 py-3 text-center text-slate-400">{s.draws}</td>
                  <td className="px-3 py-3 text-center text-rose-400">{s.losses}</td>
                  {isCricket && (
                    <>
                      <td className="px-3 py-3 text-center">{s.metrics?.runs || 0}/{s.metrics?.wickets || 0}</td>
                      <td className="px-3 py-3 text-center font-mono">{s.metrics?.nrr ? (s.metrics.nrr > 0 ? `+${s.metrics.nrr.toFixed(3)}` : s.metrics.nrr.toFixed(3)) : '0.000'}</td>
                    </>
                  )}
                  {isVolleyball && (
                    <>
                      <td className="px-3 py-3 text-center font-mono">{s.metrics?.set_diff || 0}</td>
                      <td className="px-3 py-3 text-center font-mono">1.120</td>
                    </>
                  )}
                  {!isCricket && !isVolleyball && (
                    <>
                      <td className="px-3 py-3 text-center">{s.metrics?.gf || 0}</td>
                      <td className="px-3 py-3 text-center">{s.metrics?.ga || 0}</td>
                      <td className="px-3 py-3 text-center font-mono">{s.metrics?.gd || 0}</td>
                    </>
                  )}
                  <td className="px-4 py-3 text-center font-black text-white bg-slate-850 text-sm">
                    {s.points}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

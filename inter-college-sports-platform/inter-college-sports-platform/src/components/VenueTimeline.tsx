import React from 'react';
import { Clock, AlertTriangle, FastForward } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

interface VenueTimelineProps {
  venues: { id: string; name: string; sport: string }[];
  timeSlots: string[];
  matrix: {
    [timeSlot: string]: {
      [venueId: string]: {
        id: string;
        matchLabel: string;
        teamA: string;
        teamB: string;
        status: string;
        delayedMinutes?: number;
      } | null;
    };
  };
  onCascadeDelay?: (venueId: string, minutes: number) => void;
}

export const VenueTimeline: React.FC<VenueTimelineProps> = ({
  venues,
  timeSlots,
  matrix,
  onCascadeDelay,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-x-auto shadow-xl">
      <table className="w-full text-left text-xs text-slate-300 border-collapse">
        <thead>
          <tr className="bg-slate-950 border-b border-slate-800">
            <th className="p-3.5 font-bold text-slate-400 w-32 border-r border-slate-800 flex items-center gap-1.5">
              <Clock className="w-4 h-4" /> Time Slot
            </th>
            {venues.map((v) => (
              <th key={v.id} className="p-3.5 font-bold text-white min-w-[240px] border-r border-slate-800 last:border-r-0">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="block">{v.name}</span>
                    <span className="text-[10px] text-brand-400 font-normal">{v.sport}</span>
                  </div>
                  {onCascadeDelay && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onCascadeDelay(v.id, 30)}
                      className="text-[10px] py-0.5 px-2 text-amber-300 border-amber-500/50 hover:bg-amber-950"
                    >
                      <FastForward className="w-3 h-3 mr-1" /> +30m
                    </Button>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {timeSlots.map((time) => (
            <tr key={time} className="hover:bg-slate-850/40 transition-colors">
              <td className="p-3 font-semibold text-slate-300 bg-slate-950/60 border-r border-slate-800">
                {time}
              </td>
              {venues.map((v) => {
                const match = matrix[time]?.[v.id];
                return (
                  <td key={v.id} className="p-2 border-r border-slate-800 last:border-r-0 align-top">
                    {match ? (
                      <div className="bg-slate-800 border border-slate-700 rounded-lg p-2.5 shadow-sm">
                        <div className="flex justify-between items-center mb-1.5">
                          <span className="text-[10px] font-bold text-brand-400 uppercase">{match.matchLabel}</span>
                          <Badge variant={match.status === 'LOCKED' ? 'neutral' : 'warning'}>
                            {match.status}
                          </Badge>
                        </div>
                        <div className="font-semibold text-xs text-white">
                          {match.teamA} vs {match.teamB}
                        </div>
                        {match.delayedMinutes ? (
                          <div className="flex items-center gap-1 text-[10px] text-amber-400 mt-1">
                            <AlertTriangle className="w-3 h-3" /> Delayed +{match.delayedMinutes}m
                          </div>
                        ) : null}
                      </div>
                    ) : (
                      <div className="text-[11px] text-slate-600 italic p-3 text-center">
                        Ground Available
                      </div>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

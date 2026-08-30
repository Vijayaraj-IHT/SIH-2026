'use client';

import React, { useState } from 'react';
import { ArrowLeft, RotateCcw, Award, CloudRain, ShieldCheck, Check } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export default function LiveScoringConsolePage() {
  const [scoreA, setScoreA] = useState(2);
  const [scoreB, setScoreB] = useState(1);
  const [history, setHistory] = useState<{ a: number; b: number }[]>([]);
  const [notification, setNotification] = useState<string | null>(null);

  const incrementA = () => {
    setHistory((prev) => [...prev, { a: scoreA, b: scoreB }]);
    setScoreA((prev) => prev + 1);
  };

  const incrementB = () => {
    setHistory((prev) => [...prev, { a: scoreA, b: scoreB }]);
    setScoreB((prev) => prev + 1);
  };

  const handleUndo = () => {
    if (history.length === 0) return;
    const last = history[history.length - 1];
    setScoreA(last.a);
    setScoreB(last.b);
    setHistory((prev) => prev.slice(0, -1));
  };

  const handleWalkover = () => {
    setScoreA(3);
    setScoreB(0);
    setNotification('Walkover registered: GCT awarded 3-0 default victory.');
    setTimeout(() => setNotification(null), 4000);
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
      <div className="flex justify-between items-center">
        <Link href="/scorer" className="inline-flex items-center text-xs font-semibold text-slate-400 hover:text-white gap-1">
          <ArrowLeft className="w-4 h-4" /> Exit Console
        </Link>
        <Badge variant="success">● ONLINE &amp; SYNCED</Badge>
      </div>

      {notification && (
        <div className="bg-emerald-950 border border-emerald-500 p-3 rounded-xl text-emerald-300 text-xs flex items-center gap-2">
          <Check className="w-4 h-4" /> {notification}
        </div>
      )}

      {/* Touch-Friendly Score Console */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl space-y-6">
        <div className="text-center">
          <Badge variant="info" className="mb-1">MEN&apos;S FOOTBALL • FINAL</Badge>
          <div className="text-xs text-slate-400">Main Ground (Pitch 1)</div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Team A Button Card */}
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 text-center space-y-3">
            <h3 className="font-extrabold text-sm text-white truncate">GCT</h3>
            <div className="text-6xl font-black text-brand-400 font-mono my-2">{scoreA}</div>
            <Button
              size="lg"
              variant="primary"
              onClick={incrementA}
              className="w-full py-5 text-xl font-black rounded-xl shadow-lg active:scale-95 transition-transform"
            >
              +1 GOAL
            </Button>
          </div>

          {/* Team B Button Card */}
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 text-center space-y-3">
            <h3 className="font-extrabold text-sm text-white truncate">CIT</h3>
            <div className="text-6xl font-black text-slate-200 font-mono my-2">{scoreB}</div>
            <Button
              size="lg"
              variant="secondary"
              onClick={incrementB}
              className="w-full py-5 text-xl font-black rounded-xl shadow-lg active:scale-95 transition-transform"
            >
              +1 GOAL
            </Button>
          </div>
        </div>

        {/* Quick Safety Controls */}
        <div className="flex justify-between gap-3 pt-2">
          <Button
            variant="outline"
            onClick={handleUndo}
            disabled={history.length === 0}
            className="flex-1 py-3 text-xs flex items-center justify-center gap-1.5"
          >
            <RotateCcw className="w-4 h-4" /> Undo Last Point
          </Button>

          <Button
            variant="outline"
            onClick={handleWalkover}
            className="py-3 text-xs flex items-center justify-center gap-1.5 text-amber-400 border-amber-500/40 hover:bg-amber-950"
          >
            <Award className="w-4 h-4" /> Award Walkover
          </Button>
        </div>

        {/* Lock & Submit */}
        <div className="pt-4 border-t border-slate-800">
          <Button variant="primary" className="w-full py-4 text-sm font-black flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700">
            <ShieldCheck className="w-5 h-5" /> Submit Full-Time Score &amp; Lock
          </Button>
          <span className="text-[11px] text-slate-500 block text-center mt-2">
            Locks scorecard and begins 30-minute protest window.
          </span>
        </div>
      </div>
    </div>
  );
}

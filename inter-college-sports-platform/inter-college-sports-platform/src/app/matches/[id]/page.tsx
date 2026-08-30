'use client';

import React from 'react';
import { MapPin, Calendar, Clock, Trophy, AlertCircle, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

export default function MatchDetailPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <Link href="/" className="inline-flex items-center text-xs font-semibold text-slate-400 hover:text-white gap-1 mb-2">
        <ArrowLeft className="w-4 h-4" /> Back to All Matches
      </Link>

      {/* Match Center Board */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
        <div className="bg-slate-950 px-6 py-4 border-b border-slate-800 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Badge variant="info">FOOTBALL</Badge>
            <span className="text-xs font-bold text-slate-300">FINAL MATCH</span>
          </div>
          <Badge variant="danger" className="animate-pulse">78&apos; IN PROGRESS</Badge>
        </div>

        {/* Live Score Header */}
        <div className="p-8 grid grid-cols-3 items-center text-center">
          <div className="space-y-2">
            <div className="w-16 h-16 rounded-full bg-brand-900/60 border-2 border-brand-500 mx-auto flex items-center justify-center font-black text-xl text-white shadow-lg">
              GCT
            </div>
            <h3 className="font-extrabold text-white text-lg">Govt College of Tech</h3>
            <span className="text-xs text-slate-400 font-semibold block">Coimbatore</span>
          </div>

          <div className="space-y-2">
            <div className="text-5xl font-black tracking-tight text-white flex items-center justify-center gap-3">
              <span className="text-brand-400">2</span>
              <span className="text-slate-600">-</span>
              <span className="text-slate-300">1</span>
            </div>
            <span className="text-xs font-semibold text-emerald-400 block">Live Second Half</span>
          </div>

          <div className="space-y-2">
            <div className="w-16 h-16 rounded-full bg-slate-800 border-2 border-slate-700 mx-auto flex items-center justify-center font-black text-xl text-white shadow-lg">
              CIT
            </div>
            <h3 className="font-extrabold text-white text-lg">Coimbatore Inst of Tech</h3>
            <span className="text-xs text-slate-400 font-semibold block">Coimbatore</span>
          </div>
        </div>

        {/* Match Metadata Bar */}
        <div className="bg-slate-950/80 px-6 py-3 border-t border-slate-800 flex flex-wrap justify-around text-xs text-slate-400">
          <span className="flex items-center gap-1.5"><MapPin className="w-4 h-4 text-brand-400" /> Main Ground (Pitch 1)</span>
          <span className="flex items-center gap-1.5"><Calendar className="w-4 h-4 text-slate-400" /> Today, Aug 30, 2026</span>
          <span className="flex items-center gap-1.5"><Clock className="w-4 h-4 text-slate-400" /> Kick-off: 02:00 PM IST</span>
        </div>
      </div>

      {/* Match Timeline / Incident Log */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
        <h4 className="font-bold text-sm text-white mb-4 flex items-center gap-2">
          <Clock className="w-4 h-4 text-brand-400" /> Match Events & Timeline
        </h4>
        <div className="space-y-3 text-xs">
          <div className="flex items-start gap-3 p-2 rounded bg-slate-850">
            <span className="font-bold text-brand-400 w-8">72&apos;</span>
            <span className="text-slate-200">⚽ <strong>GOAL!</strong> M. Suresh scores for GCT (Assisted by K. Praveen)</span>
          </div>
          <div className="flex items-start gap-3 p-2 rounded bg-slate-850">
            <span className="font-bold text-brand-400 w-8">45&apos;</span>
            <span className="text-slate-400">Halftime: GCT 1 - 1 CIT</span>
          </div>
          <div className="flex items-start gap-3 p-2 rounded bg-slate-850">
            <span className="font-bold text-brand-400 w-8">34&apos;</span>
            <span className="text-slate-200">⚽ <strong>GOAL!</strong> R. Arun scores for CIT</span>
          </div>
          <div className="flex items-start gap-3 p-2 rounded bg-slate-850">
            <span className="font-bold text-brand-400 w-8">12&apos;</span>
            <span className="text-slate-200">⚽ <strong>GOAL!</strong> M. Suresh opens the scoring for GCT</span>
          </div>
        </div>
      </div>
    </div>
  );
}

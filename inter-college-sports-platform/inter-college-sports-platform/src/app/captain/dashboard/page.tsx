'use client';

import React, { useState } from 'react';
import { Calendar, MapPin, Clock, CheckCircle, AlertCircle, ShieldAlert } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export default function CaptainDashboardPage() {
  const [checkedIn, setCheckedIn] = useState(false);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 text-brand-400 text-xs font-bold uppercase tracking-wider mb-1">
            <Calendar className="w-4 h-4" /> Team Representative Portal
          </div>
          <h1 className="text-2xl font-extrabold text-white">
            GCT Men&apos;s Football Hub
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Captain: M. Suresh (22GCT101) • Eligibility Status: <strong className="text-emerald-400">VERIFIED ✅</strong>
          </p>
        </div>
      </div>

      {/* "My Match Day" Active Card */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-850 to-slate-950 border border-brand-500/50 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <Badge variant="success" className="mb-2">MATCH DAY ACTIVE</Badge>
            <h2 className="text-xl sm:text-2xl font-extrabold text-white">
              Semi Final 1 vs Coimbatore Institute of Technology
            </h2>
          </div>
          <Badge variant="warning">ON SCHEDULE 🟢</Badge>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs">
          <div>
            <span className="text-slate-400 block mb-1">Assigned Pitch</span>
            <strong className="text-white text-sm flex items-center gap-1">
              <MapPin className="w-4 h-4 text-brand-400" /> Main Ground (Pitch 1)
            </strong>
          </div>
          <div>
            <span className="text-slate-400 block mb-1">Reporting Call-in</span>
            <strong className="text-amber-400 text-sm flex items-center gap-1">
              <Clock className="w-4 h-4" /> 01:20 PM IST (Mandatory)
            </strong>
          </div>
          <div>
            <span className="text-slate-400 block mb-1">Scheduled Kick-off</span>
            <strong className="text-white text-sm flex items-center gap-1">
              <Calendar className="w-4 h-4" /> 02:00 PM IST
            </strong>
          </div>
        </div>

        {/* 1-Tap Check-In */}
        {!checkedIn ? (
          <Button
            size="lg"
            variant="primary"
            onClick={() => setCheckedIn(true)}
            className="w-full py-4 text-sm font-extrabold shadow-xl flex items-center justify-center gap-2"
          >
            <CheckCircle className="w-5 h-5" /> TAP TO CONFIRM TEAM ARRIVAL AT GROUND
          </Button>
        ) : (
          <div className="bg-emerald-950/80 border border-emerald-500/60 p-4 rounded-xl text-emerald-300 text-xs font-semibold flex items-center justify-between">
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4" /> Team Arrival Confirmed with Ground Desk.
            </span>
            <span className="text-[10px] text-slate-400">01:18 PM IST</span>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
          <Link href="/captain/lineup/m1">
            <Button variant="outline" className="w-full py-3 text-xs flex items-center justify-center gap-1.5">
              👥 Submit Starting 11 Lineup
            </Button>
          </Link>
          <Link href="/captain/protest/m1">
            <Button variant="outline" className="w-full py-3 text-xs flex items-center justify-center gap-1.5 text-rose-400 border-rose-500/40 hover:bg-rose-950">
              <ShieldAlert className="w-4 h-4" /> Submit Match Protest (30m Window)
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

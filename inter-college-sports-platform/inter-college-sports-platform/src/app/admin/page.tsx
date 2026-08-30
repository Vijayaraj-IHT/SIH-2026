'use client';

import React from 'react';
import Link from 'next/link';
import { ShieldAlert, Calendar, UserCheck, AlertTriangle, FileText, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export default function AdminDashboardPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-xl">
        <div>
          <div className="flex items-center gap-2 text-amber-400 text-xs font-bold uppercase tracking-wider mb-2">
            <ShieldAlert className="w-4 h-4" /> Convener &amp; Physical Director Panel
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            Master Tournament Control Desk
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time venue management, conflict resolution, spot registration, and protest adjudication.
          </p>
        </div>
        <div className="flex gap-3">
          <Link href="/admin/scheduler">
            <Button variant="primary" className="flex items-center gap-2">
              <Calendar className="w-4 h-4" /> Open Scheduler Matrix
            </Button>
          </Link>
        </div>
      </div>

      {/* Operational KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <span className="text-xs text-slate-400 font-semibold uppercase">Active Venues</span>
          <div className="text-2xl font-black text-white mt-1">4 / 4 In Use</div>
          <span className="text-[11px] text-emerald-400 mt-1 block">0 Conflicts Detected</span>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <span className="text-xs text-slate-400 font-semibold uppercase">Pending Roster Approvals</span>
          <div className="text-2xl font-black text-amber-400 mt-1">2 Teams</div>
          <Link href="/admin/approvals" className="text-[11px] text-brand-400 hover:underline mt-1 block">
            Review Documents →
          </Link>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <span className="text-xs text-slate-400 font-semibold uppercase">Protests Under Review</span>
          <div className="text-2xl font-black text-rose-400 mt-1">1 Case</div>
          <Link href="/admin/disputes" className="text-[11px] text-rose-400 hover:underline mt-1 block">
            Adjudicate with Jury →
          </Link>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <span className="text-xs text-slate-400 font-semibold uppercase">Matches Completed</span>
          <div className="text-2xl font-black text-slate-200 mt-1">18 / 32</div>
          <span className="text-[11px] text-slate-400 mt-1 block">56% Progress</span>
        </div>
      </div>

      {/* Admin Modules Navigation */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link href="/admin/scheduler" className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-brand-500 transition-all shadow-lg block">
          <Calendar className="w-8 h-8 text-brand-400 mb-3" />
          <h3 className="text-lg font-bold text-white mb-1">Visual Timetable &amp; Delays</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Drag-and-drop matches across grounds and courts. Apply one-click +30m cascade delays for rain or overtime.
          </p>
        </Link>

        <Link href="/admin/approvals" className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-brand-500 transition-all shadow-lg block">
          <UserCheck className="w-8 h-8 text-amber-400 mb-3" />
          <h3 className="text-lg font-bold text-white mb-1">Registration &amp; Spot Entry</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Verify student ID cards, approve bonafide rosters, or spot-register walk-in visiting teams in 60 seconds.
          </p>
        </Link>

        <Link href="/admin/disputes" className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-brand-500 transition-all shadow-lg block">
          <AlertTriangle className="w-8 h-8 text-rose-400 mb-3" />
          <h3 className="text-lg font-bold text-white mb-1">Dispute Adjudication</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Review official match protests, log sports jury deliberations, and execute versioned score corrections.
          </p>
        </Link>
      </div>
    </div>
  );
}

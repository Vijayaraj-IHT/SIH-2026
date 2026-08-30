'use client';

import React from 'react';
import { FileText, ArrowLeft, Shield } from 'lucide-react';
import Link from 'next/link';
import { Badge } from '@/components/ui/Badge';

export default function AdminAuditLogPage() {
  const auditEntries = [
    {
      id: 'aud-001',
      action: 'result.locked',
      subject_type: 'MATCH_RESULT',
      actor: 'Dr. R. Ramanathan (Super Admin)',
      timestamp: '2026-08-30 14:40:00 IST',
      detail: 'Locked final score GCT 2 - 1 CIT. Triggered standings recompute and advancement.',
    },
    {
      id: 'aud-002',
      action: 'fixture.rescheduled',
      subject_type: 'FIXTURE',
      actor: 'System / Cascade Delay',
      timestamp: '2026-08-30 12:15:00 IST',
      detail: 'Shifted Pitch 1 matches forward by +30 minutes due to morning rain delay.',
    },
    {
      id: 'aud-003',
      action: 'team.verified',
      subject_type: 'TEAM',
      actor: 'Dr. R. Ramanathan (Super Admin)',
      timestamp: '2026-08-30 08:45:00 IST',
      detail: 'Verified bonafide roster for GCT Men Football (14 players approved).',
    },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      <Link href="/admin" className="inline-flex items-center text-xs font-semibold text-slate-400 hover:text-white gap-1">
        <ArrowLeft className="w-4 h-4" /> Back to Admin Panel
      </Link>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl">
        <div className="flex justify-between items-center mb-6">
          <div>
            <div className="flex items-center gap-2 text-brand-400 text-xs font-bold uppercase tracking-wider mb-1">
              <Shield className="w-4 h-4" /> Immutable Audit Trail
            </div>
            <h1 className="text-2xl font-extrabold text-white">System Audit Log</h1>
          </div>
          <Badge variant="neutral">Append-Only Store</Badge>
        </div>

        <div className="space-y-3">
          {auditEntries.map((a) => (
            <div key={a.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
              <div className="flex justify-between items-center">
                <span className="font-mono font-bold text-brand-400">{a.action}</span>
                <span className="text-slate-500 font-mono text-[10px]">{a.timestamp}</span>
              </div>
              <div className="text-slate-300 font-semibold">{a.detail}</div>
              <div className="text-slate-500 text-[11px]">Actor: {a.actor} • Subject: {a.subject_type}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

'use client';

import React, { useState } from 'react';
import { AlertTriangle, CheckCircle, XCircle, ArrowLeft, Shield } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export default function AdminDisputesPage() {
  const [juryNotes, setJuryNotes] = useState('');
  const [actionSummary, setActionSummary] = useState('');
  const [resolved, setResolved] = useState(false);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <Link href="/admin" className="inline-flex items-center text-xs font-semibold text-slate-400 hover:text-white gap-1">
        <ArrowLeft className="w-4 h-4" /> Back to Admin Panel
      </Link>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-2 text-rose-400 text-xs font-bold uppercase tracking-wider mb-1">
              <AlertTriangle className="w-4 h-4" /> Official Protest Case #PRO-2026-001
            </div>
            <h1 className="text-2xl font-extrabold text-white">
              Dispute Adjudication Console
            </h1>
          </div>
          <Badge variant={resolved ? 'neutral' : 'danger'}>
            {resolved ? 'ADJUDICATED' : 'UNDER_DISPUTE'}
          </Badge>
        </div>

        {/* Match Context Card */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs space-y-2">
          <div className="flex justify-between font-semibold text-slate-300">
            <span>Match: Men&apos;s Football Semi-Final 1</span>
            <span>Ground: Main Pitch 1</span>
          </div>
          <div className="text-slate-400">
            Protesting Team: <strong className="text-white">PSG Tech</strong> vs Winner: <strong className="text-white">GCT (2-1)</strong>
          </div>
          <div className="text-slate-400">
            Filing Reason: <strong className="text-rose-400">ELIGIBILITY - Ineligible Player #7</strong>
          </div>
          <div className="p-3 bg-slate-900 rounded border border-slate-800 text-slate-200 mt-2">
            &quot;Player #7 of GCT was not on the verified pre-match bonafide roster submitted during registration.&quot;
          </div>
        </div>

        {/* Jury Decision Form */}
        {!resolved ? (
          <div className="space-y-4 pt-2">
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              <Shield className="w-4 h-4 text-brand-400" /> Sports Jury Resolution &amp; Audit Metadata
            </h3>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Jury Convener &amp; Members Present
              </label>
              <input
                type="text"
                defaultValue="Dr. R. Ramanathan (Chief), Prof. S. Balaji, Ref. M. Kumar"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Jury Deliberation Notes
              </label>
              <textarea
                rows={3}
                placeholder="State the verified physical evidence, ID card review, or match sheet findings..."
                value={juryNotes}
                onChange={(e) => setJuryNotes(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <Button variant="danger" onClick={() => setResolved(true)}>
                <XCircle className="w-4 h-4 mr-1.5" /> Dismiss Protest (Maintain 2-1 Score)
              </Button>
              <Button variant="primary" onClick={() => setResolved(true)}>
                <CheckCircle className="w-4 h-4 mr-1.5" /> Upheld: Overturn Result &amp; Recompute
              </Button>
            </div>
          </div>
        ) : (
          <div className="bg-emerald-950/40 border border-emerald-500/50 p-4 rounded-xl text-emerald-300 text-xs">
            ✓ Protest decision officially logged to immutable Audit Trail. Standings and downstream brackets updated.
          </div>
        )}
      </div>
    </div>
  );
}

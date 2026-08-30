'use client';

import React, { useState } from 'react';
import { ArrowLeft, AlertTriangle, ShieldAlert, CheckCircle } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export default function CaptainProtestPage() {
  const [reasonCategory, setReasonCategory] = useState('ELIGIBILITY');
  const [description, setDescription] = useState('');
  const [filed, setFiled] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFiled(true);
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      <Link href="/captain/dashboard" className="inline-flex items-center text-xs font-semibold text-slate-400 hover:text-white gap-1">
        <ArrowLeft className="w-4 h-4" /> Back to Captain Dashboard
      </Link>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-2 text-rose-400 text-xs font-bold uppercase tracking-wider mb-1">
              <ShieldAlert className="w-4 h-4" /> Official Dispute Filing
            </div>
            <h1 className="text-xl font-extrabold text-white">
              Lodge Match Protest (30-Minute Window)
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Per Tournament Rule 2.20, protests must be submitted within 30 minutes of match scorecard submission.
            </p>
          </div>
          <Badge variant="danger">Window: 18m Left</Badge>
        </div>

        {filed ? (
          <div className="bg-emerald-950/80 border border-emerald-500/60 p-5 rounded-xl text-emerald-300 text-xs space-y-2">
            <div className="flex items-center gap-2 font-bold text-sm">
              <CheckCircle className="w-5 h-5 text-emerald-400" /> Protest Case Logged Successfully
            </div>
            <p className="text-slate-300">
              Your protest has been assigned reference ID <code>PRO-2026-002</code>. 
              The downstream match has been placed on <strong>HELD_FOR_DISPUTE</strong> pending Sports Jury review.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Dispute Reason Category</label>
              <select
                value={reasonCategory}
                onChange={(e) => setReasonCategory(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-brand-500"
              >
                <option value="ELIGIBILITY">Player Eligibility / Non-Bonafide Impersonation</option>
                <option value="SCORING_ERROR">Scoring Discrepancy / Mathematical Error</option>
                <option value="OFFICIATING">Officiating Misconduct / Rule Violation</option>
                <option value="OTHER">Other Ground Dispute</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-semibold mb-1">Detailed Description of Grievance</label>
              <textarea
                required
                rows={4}
                placeholder="State player names, jersey numbers, incident minute, or specific rule violations witnessed..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-brand-500"
              />
            </div>

            <Button variant="danger" type="submit" className="w-full py-3 text-xs font-bold flex items-center justify-center gap-2">
              <AlertTriangle className="w-4 h-4" /> Submit Official Protest to Sports Jury
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}

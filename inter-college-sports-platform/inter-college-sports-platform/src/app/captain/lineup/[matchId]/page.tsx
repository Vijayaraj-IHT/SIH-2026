'use client';

import React, { useState } from 'react';
import { ArrowLeft, CheckCircle, ShieldCheck } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export default function CaptainLineupPage() {
  const [selectedIds, setSelectedIds] = useState<string[]>(['1', '2', '3', '4', '5']);
  const [submitted, setSubmitted] = useState(false);

  const players = [
    { id: '1', rollNo: '22GCT101', name: 'M. Suresh (Captain)', jersey: 10, pos: 'Forward' },
    { id: '2', rollNo: '22GCT102', name: 'K. Praveen', jersey: 1, pos: 'Goalkeeper' },
    { id: '3', rollNo: '22GCT103', name: 'S. Aravind', jersey: 4, pos: 'Defender' },
    { id: '4', rollNo: '22GCT104', name: 'V. Dinesh', jersey: 7, pos: 'Midfielder' },
    { id: '5', rollNo: '22GCT105', name: 'R. Karthi', jersey: 11, pos: 'Forward' },
    { id: '6', rollNo: '22GCT106', name: 'T. Naveen', jersey: 8, pos: 'Midfielder (Sub)' },
  ];

  const togglePlayer = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <Link href="/captain/dashboard" className="inline-flex items-center text-xs font-semibold text-slate-400 hover:text-white gap-1">
        <ArrowLeft className="w-4 h-4" /> Back to Captain Dashboard
      </Link>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <Badge variant="info" className="mb-1">PRE-MATCH SUBMISSION</Badge>
            <h1 className="text-xl font-extrabold text-white">Starting Lineup Selection</h1>
            <p className="text-xs text-slate-400 mt-1">
              Select verified squad members for Semi-Final 1 vs CIT. Locked 30 mins before kick-off.
            </p>
          </div>
          <Badge variant="success">{selectedIds.length} Selected</Badge>
        </div>

        {submitted ? (
          <div className="bg-emerald-950/80 border border-emerald-500/60 p-4 rounded-xl text-emerald-300 text-xs font-semibold flex items-center gap-2">
            <CheckCircle className="w-5 h-5" /> Official starting lineup locked and transmitted to Ground Scorer Desk.
          </div>
        ) : (
          <div className="space-y-3">
            {players.map((p) => (
              <label
                key={p.id}
                className={`flex items-center justify-between p-3.5 rounded-xl border cursor-pointer transition-colors ${
                  selectedIds.includes(p.id)
                    ? 'bg-slate-800 border-brand-500/60 text-white'
                    : 'bg-slate-950 border-slate-800 text-slate-400'
                }`}
              >
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(p.id)}
                    onChange={() => togglePlayer(p.id)}
                    className="w-4 h-4 rounded text-brand-600 focus:ring-brand-500"
                  />
                  <div>
                    <span className="font-bold text-xs block">{p.name}</span>
                    <span className="text-[11px] text-slate-400">Roll: {p.rollNo} • Pos: {p.pos}</span>
                  </div>
                </div>
                <span className="font-mono text-xs font-bold text-brand-400">#{p.jersey}</span>
              </label>
            ))}

            <Button
              variant="primary"
              onClick={() => setSubmitted(true)}
              className="w-full py-3.5 text-xs font-bold flex items-center justify-center gap-2 mt-4"
            >
              <ShieldCheck className="w-4 h-4" /> Transmit &amp; Lock Match Lineup
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

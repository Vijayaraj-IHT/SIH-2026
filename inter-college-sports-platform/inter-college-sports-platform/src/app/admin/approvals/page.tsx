'use client';

import React, { useState } from 'react';
import { UserCheck, Plus, CheckCircle, XCircle, ArrowLeft, ShieldAlert } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export default function AdminApprovalsPage() {
  const [showSpotModal, setShowSpotModal] = useState(false);
  const [spotCollege, setSpotCollege] = useState('');
  const [spotSport, setSpotSport] = useState('FOOTBALL');
  const [spotCaptainPhone, setSpotCaptainPhone] = useState('');

  const [pendingTeams, setPendingTeams] = useState([
    { id: '1', college: 'Thiagarajar College of Engg (TCE)', sport: "Men's Volleyball", route: 'ADVANCE', playersCount: 12, bonafideUploaded: true },
    { id: '2', college: 'Alagappa Chettiar College (ACC)', sport: "Men's Football", route: 'SPOT', playersCount: 14, bonafideUploaded: false },
  ]);

  const handleApprove = (id: string) => {
    setPendingTeams((prev) => prev.filter((t) => t.id !== id));
  };

  const handleSpotRegister = (e: React.FormEvent) => {
    e.preventDefault();
    setPendingTeams((prev) => [
      ...prev,
      {
        id: String(Date.now()),
        college: spotCollege,
        sport: spotSport,
        route: 'SPOT',
        playersCount: 11,
        bonafideUploaded: false,
      },
    ]);
    setShowSpotModal(false);
    setSpotCollege('');
    setSpotCaptainPhone('');
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <Link href="/admin" className="inline-flex items-center text-xs font-semibold text-slate-400 hover:text-white gap-1">
        <ArrowLeft className="w-4 h-4" /> Back to Admin Panel
      </Link>

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <UserCheck className="w-6 h-6 text-amber-400" /> Team Registration &amp; Spot Verification Desk
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Review student eligibility documents or perform 60-second spot registration for walk-in teams.
          </p>
        </div>
        <Button variant="primary" onClick={() => setShowSpotModal(true)} className="flex items-center gap-1.5">
          <Plus className="w-4 h-4" /> 60s Spot Entry Modal
        </Button>
      </div>

      {/* Pending Teams List */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
            <tr>
              <th className="p-4 font-bold">College / Institution</th>
              <th className="p-4 font-bold">Sport</th>
              <th className="p-4 font-bold">Route</th>
              <th className="p-4 font-bold">Roster Size</th>
              <th className="p-4 font-bold">Bonafide Letter</th>
              <th className="p-4 font-bold text-right">Verification Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {pendingTeams.map((t) => (
              <tr key={t.id} className="hover:bg-slate-850/50">
                <td className="p-4 font-semibold text-white">{t.college}</td>
                <td className="p-4"><Badge variant="info">{t.sport}</Badge></td>
                <td className="p-4"><Badge variant={t.route === 'SPOT' ? 'warning' : 'neutral'}>{t.route}</Badge></td>
                <td className="p-4">{t.playersCount} Players</td>
                <td className="p-4">
                  {t.bonafideUploaded ? (
                    <span className="text-emerald-400 font-semibold">Verified Upload</span>
                  ) : (
                    <span className="text-amber-400 font-semibold">Check Physical ID on Ground</span>
                  )}
                </td>
                <td className="p-4 text-right space-x-2">
                  <Button size="sm" variant="primary" onClick={() => handleApprove(t.id)}>
                    <CheckCircle className="w-3.5 h-3.5 mr-1" /> Approve
                  </Button>
                  <Button size="sm" variant="danger" onClick={() => handleApprove(t.id)}>
                    <XCircle className="w-3.5 h-3.5 mr-1" /> Reject
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 60-Second Spot Entry Modal */}
      {showSpotModal && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="font-extrabold text-lg text-white flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-400" /> Express 60s Spot Registration
            </h3>
            <p className="text-xs text-slate-400">
              Instantly create a provisional team entry so fixture draws are not delayed. Physical ID checks occur at ground.
            </p>

            <form onSubmit={handleSpotRegister} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">College Name &amp; Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. PSG College of Tech (PSG)"
                  value={spotCollege}
                  onChange={(e) => setSpotCollege(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Sport Category</label>
                <select
                  value={spotSport}
                  onChange={(e) => setSpotSport(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-brand-500"
                >
                  <option value="FOOTBALL">Football (Men)</option>
                  <option value="VOLLEYBALL">Volleyball (Men)</option>
                  <option value="CRICKET">Cricket (Men)</option>
                  <option value="BADMINTON">Badminton (Women)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Captain Mobile Number (SMS Alerts)</label>
                <input
                  type="tel"
                  required
                  placeholder="+91 98765 43210"
                  value={spotCaptainPhone}
                  onChange={(e) => setSpotCaptainPhone(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <Button variant="ghost" type="button" onClick={() => setShowSpotModal(false)}>
                  Cancel
                </Button>
                <Button variant="primary" type="submit">
                  Confirm &amp; Seed Team
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

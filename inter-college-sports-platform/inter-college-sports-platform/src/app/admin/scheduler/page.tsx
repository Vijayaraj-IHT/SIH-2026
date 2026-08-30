'use client';

import React, { useState } from 'react';
import { Calendar, FastForward, CheckCircle2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { VenueTimeline } from '@/components/VenueTimeline';
import { Button } from '@/components/ui/Button';

export default function AdminSchedulerPage() {
  const [notification, setNotification] = useState<string | null>(null);

  const venues = [
    { id: 'v1', name: 'Main Ground (Pitch 1)', sport: 'Football & Cricket' },
    { id: 'v2', name: 'Indoor Stadium (Court 1)', sport: 'Volleyball & Basketball' },
    { id: 'v3', name: 'Badminton Arena (Court A)', sport: 'Badminton' },
  ];

  const timeSlots = ['08:30 AM', '10:00 AM', '11:30 AM', '02:00 PM', '03:30 PM'];

  const matrix = {
    '08:30 AM': {
      v1: { id: 'm1', matchLabel: 'QF 1', teamA: 'GCT', teamB: 'TCE', status: 'LOCKED' },
      v2: { id: 'm2', matchLabel: 'Pool A', teamA: 'PSG', teamB: 'CIT', status: 'LOCKED' },
      v3: { id: 'm3', matchLabel: 'R16', teamA: 'MIT', teamB: 'ACC', status: 'LOCKED' },
    },
    '10:00 AM': {
      v1: { id: 'm4', matchLabel: 'QF 2', teamA: 'CIT', teamB: 'ACC', status: 'LOCKED' },
      v2: { id: 'm5', matchLabel: 'Pool B', teamA: 'GCT', teamB: 'TCE', status: 'IN_PROGRESS' },
      v3: null,
    },
    '11:30 AM': {
      v1: { id: 'm6', matchLabel: 'QF 3', teamA: 'PSG', teamB: 'KCT', status: 'IN_PROGRESS' },
      v2: { id: 'm7', matchLabel: 'Pool A', teamA: 'MIT', teamB: 'CIT', status: 'SCHEDULED' },
      v3: { id: 'm8', matchLabel: 'QF 1', teamA: 'PSG', teamB: 'GCT', status: 'SCHEDULED' },
    },
    '02:00 PM': {
      v1: { id: 'm9', matchLabel: 'SEMI FINAL 1', teamA: 'GCT', teamB: 'CIT', status: 'SCHEDULED' },
      v2: { id: 'm10', matchLabel: 'SEMI FINAL 1', teamA: 'TBD', teamB: 'TBD', status: 'SCHEDULED' },
      v3: null,
    },
    '03:30 PM': {
      v1: { id: 'm11', matchLabel: 'FINAL MATCH', teamA: 'TBD', teamB: 'TBD', status: 'SCHEDULED' },
      v2: null,
      v3: { id: 'm12', matchLabel: 'FINAL', teamA: 'TBD', teamB: 'TBD', status: 'SCHEDULED' },
    },
  };

  const handleCascadeDelay = (venueId: string, mins: number) => {
    setNotification(`Successfully shifted remaining matches on venue by +${mins} minutes! Notifications broadcast to Captains.`);
    setTimeout(() => setNotification(null), 4000);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <Link href="/admin" className="inline-flex items-center text-xs font-semibold text-slate-400 hover:text-white gap-1">
        <ArrowLeft className="w-4 h-4" /> Back to Admin Panel
      </Link>

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <Calendar className="w-6 h-6 text-brand-400" /> Interactive Venue Timetable Matrix
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Manage grounds, detect time clashes, and apply 1-click cascade delays.
          </p>
        </div>
      </div>

      {notification && (
        <div className="bg-emerald-950/90 border border-emerald-500/60 p-4 rounded-xl text-emerald-300 text-xs flex items-center gap-2 shadow-lg animate-fade-in">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{notification}</span>
        </div>
      )}

      <VenueTimeline
        venues={venues}
        timeSlots={timeSlots}
        matrix={matrix as any}
        onCascadeDelay={handleCascadeDelay}
      />
    </div>
  );
}

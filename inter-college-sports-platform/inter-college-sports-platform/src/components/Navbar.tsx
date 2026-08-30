'use client';

import React from 'react';
import Link from 'next/link';
import { Trophy, Calendar, Users, ShieldAlert, Award, Radio } from 'lucide-react';

export const Navbar: React.FC = () => {
  return (
    <header className="sticky top-0 z-50 bg-slate-900 border-b border-slate-800 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo */}
          <Link href="/" className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-brand-600 flex items-center justify-center font-bold text-xl text-white shadow-md">
              <Trophy className="w-6 h-6" />
            </div>
            <div>
              <span className="font-extrabold text-lg tracking-tight text-white block leading-none">
                CAMPUS<span className="text-brand-500">ARENA</span>
              </span>
              <span className="text-[10px] text-slate-400 font-medium tracking-widest uppercase block mt-0.5">
                Inter-Collegiate Fixtures
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-6">
            <Link href="/" className="text-sm font-medium text-slate-200 hover:text-brand-400 flex items-center gap-1.5 transition-colors">
              <Calendar className="w-4 h-4" /> Fixtures & Results
            </Link>
            <Link href="/leaderboard" className="text-sm font-medium text-slate-200 hover:text-brand-400 flex items-center gap-1.5 transition-colors">
              <Award className="w-4 h-4" /> Overall Trophy
            </Link>
            <Link href="/captain/dashboard" className="text-sm font-medium text-slate-200 hover:text-brand-400 flex items-center gap-1.5 transition-colors">
              <Users className="w-4 h-4" /> Captain Portal
            </Link>
            <Link href="/scorer" className="text-sm font-medium text-slate-200 hover:text-brand-400 flex items-center gap-1.5 transition-colors">
              <Radio className="w-4 h-4 text-emerald-400 animate-pulse" /> Field Scorer
            </Link>
            <Link href="/admin" className="text-sm font-medium text-slate-200 hover:text-brand-400 flex items-center gap-1.5 transition-colors">
              <ShieldAlert className="w-4 h-4 text-amber-400" /> Admin Desk
            </Link>
          </nav>

          {/* Live Indicator / Action */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center gap-2 bg-slate-800 border border-slate-700 px-3 py-1.5 rounded-full text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
              <span className="text-slate-300">MEET 2026 LIVE</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

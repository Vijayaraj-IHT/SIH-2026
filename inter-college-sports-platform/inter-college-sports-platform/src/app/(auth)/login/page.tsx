'use client';

import React, { useState } from 'react';
import { Trophy, Lock, Mail, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.includes('admin')) {
      window.location.href = '/admin';
    } else if (email.includes('scorer')) {
      window.location.href = '/scorer';
    } else {
      window.location.href = '/captain/dashboard';
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-md w-full p-8 space-y-6 shadow-2xl">
        <div className="text-center">
          <div className="w-12 h-12 bg-brand-600 rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-lg">
            <Trophy className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-2xl font-black text-white">Sign In to Campus Arena</h2>
          <p className="text-xs text-slate-400 mt-1">
            Enter your sports authority or captain credentials
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-semibold mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="email"
                required
                placeholder="e.g. admin.sports@gct.ac.in"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 pl-9 pr-3 text-white focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 pl-9 pr-3 text-white focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>

          <Button variant="primary" type="submit" className="w-full py-3 text-sm font-bold flex items-center justify-center gap-2">
            Sign In <ArrowRight className="w-4 h-4" />
          </Button>
        </form>

        <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-[11px] text-slate-400 space-y-1">
          <p className="font-semibold text-slate-300">Quick Test Credentials:</p>
          <p>• Admin: <code className="text-amber-400">admin@gct.ac.in</code></p>
          <p>• Scorer: <code className="text-emerald-400">scorer@gct.ac.in</code></p>
          <p>• Captain: <code className="text-brand-400">captain@gct.ac.in</code></p>
        </div>
      </div>
    </div>
  );
}

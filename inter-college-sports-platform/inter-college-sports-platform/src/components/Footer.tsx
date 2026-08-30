import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-950 text-slate-400 border-t border-slate-900 py-8 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center sm:text-left flex flex-col sm:flex-row justify-between items-center gap-4">
        <div>
          <p className="text-sm font-medium text-slate-300">
            Inter-Collegiate Sports Meet & Fixtures Management System
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Compliant with Domain Specification v1.3 • Supabase PostgreSQL • Real-Time Scoring
          </p>
        </div>
        <div className="text-xs text-slate-500">
          © 2026 Sports Board Committee. All Rights Reserved.
        </div>
      </div>
    </footer>
  );
};

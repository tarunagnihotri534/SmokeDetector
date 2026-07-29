'use client';

import React from 'react';
import { Users, AlertTriangle, ShieldCheck, Flame } from 'lucide-react';
import { StreamStats } from '@/lib/useLiveSocket';

interface StatsCardsProps {
  stats?: StreamStats;
}

export const StatsCards: React.FC<StatsCardsProps> = ({ stats }) => {
  const total = stats?.total_persons ?? 0;
  const smoking = stats?.smoking ?? 0;
  const safe = stats?.safe ?? 0;
  const violations = stats?.violations ?? 0;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Persons */}
      <div className="glass-panel p-4 rounded-xl flex items-center justify-between border-l-4 border-l-sky-500">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Persons</p>
          <p className="text-2xl font-bold text-slate-100 mt-1">{total}</p>
        </div>
        <div className="p-3 bg-sky-500/10 rounded-lg text-sky-400">
          <Users className="w-6 h-6" />
        </div>
      </div>

      {/* Safe */}
      <div className="glass-panel p-4 rounded-xl flex items-center justify-between border-l-4 border-l-emerald-500">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Safe</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">{safe}</p>
        </div>
        <div className="p-3 bg-emerald-500/10 rounded-lg text-emerald-400">
          <ShieldCheck className="w-6 h-6" />
        </div>
      </div>

      {/* Smoking (Pending Debounce) */}
      <div className="glass-panel p-4 rounded-xl flex items-center justify-between border-l-4 border-l-amber-500">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Smoking</p>
          <p className="text-2xl font-bold text-amber-400 mt-1">{smoking}</p>
        </div>
        <div className="p-3 bg-amber-500/10 rounded-lg text-amber-400">
          <Flame className="w-6 h-6" />
        </div>
      </div>

      {/* Violations */}
      <div className={`glass-panel p-4 rounded-xl flex items-center justify-between border-l-4 border-l-rose-500 ${violations > 0 ? 'bg-rose-950/30' : ''}`}>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Violations</p>
          <p className="text-2xl font-bold text-rose-500 mt-1">{violations}</p>
        </div>
        <div className="p-3 bg-rose-500/10 rounded-lg text-rose-400">
          <AlertTriangle className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
};

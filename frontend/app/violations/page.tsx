'use client';

import React, { useState, useEffect } from 'react';
import { Filter, RefreshCw, FileText } from 'lucide-react';
import { ViolationTable } from '@/components/ViolationTable';
import { fetchViolations, fetchViolationStats, ViolationRecord } from '@/lib/api';

export default function ViolationsPage() {
  const [violations, setViolations] = useState<ViolationRecord[]>([]);
  const [cameraIdFilter, setCameraIdFilter] = useState<string>('');
  const [stats, setStats] = useState({ total_violations: 0, violations_today: 0, active_violations: 0 });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [recs, st] = await Promise.all([
        fetchViolations(cameraIdFilter || undefined, 100),
        fetchViolationStats(),
      ]);
      setViolations(recs);
      setStats(st);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [cameraIdFilter]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-6 rounded-2xl border-l-4 border-l-rose-500">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-100 flex items-center gap-2">
            <FileText className="w-6 h-6 text-rose-500" />
            Violation Audit Log & Analytics
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Historical records, timestamps, track IDs, and captured evidence snapshots.
          </p>
        </div>

        {/* Top Summary Metrics */}
        <div className="flex items-center space-x-4">
          <div className="bg-slate-900/80 px-4 py-2 rounded-xl border border-slate-800 text-center">
            <p className="text-[10px] font-mono uppercase text-slate-400">Total Logged</p>
            <p className="text-xl font-bold text-slate-100">{stats.total_violations}</p>
          </div>
          <div className="bg-slate-900/80 px-4 py-2 rounded-xl border border-slate-800 text-center">
            <p className="text-[10px] font-mono uppercase text-slate-400">Today</p>
            <p className="text-xl font-bold text-rose-400">{stats.violations_today}</p>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="glass-panel p-4 rounded-xl flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-bold text-slate-300">Filter by Camera:</span>
          <input
            type="text"
            placeholder="e.g. cam-01"
            value={cameraIdFilter}
            onChange={(e) => setCameraIdFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs text-slate-200 px-3 py-1.5 rounded-lg focus:outline-none focus:border-rose-500"
          />
        </div>

        <button
          onClick={loadData}
          disabled={isLoading}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold rounded-lg transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Violation Data Table */}
      <ViolationTable violations={violations} onRefresh={loadData} />
    </div>
  );
}

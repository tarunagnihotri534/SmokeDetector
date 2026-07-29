'use client';

import React, { useState } from 'react';
import { Download, ExternalLink, Camera, Clock, Tag } from 'lucide-react';
import { ViolationRecord, getSnapshotUrl, getExportUrl } from '@/lib/api';

interface ViolationTableProps {
  violations: ViolationRecord[];
  onRefresh?: () => void;
}

export const ViolationTable: React.FC<ViolationTableProps> = ({ violations }) => {
  const [selectedSnapshot, setSelectedSnapshot] = useState<string | null>(null);

  return (
    <div className="glass-panel rounded-xl overflow-hidden">
      {/* Table Header Controls */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
          <span>Violation History Log</span>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
            {violations.length} records
          </span>
        </h3>
        <a
          href={getExportUrl()}
          download
          className="inline-flex items-center space-x-2 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg transition"
        >
          <Download className="w-4 h-4" />
          <span>Export CSV</span>
        </a>
      </div>

      {/* Table Body */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-900/60 text-slate-400 uppercase font-mono text-xs border-b border-slate-800">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Camera</th>
              <th className="px-4 py-3">Track ID</th>
              <th className="px-4 py-3">Started At</th>
              <th className="px-4 py-3">Status / Duration</th>
              <th className="px-4 py-3">Snapshot</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {violations.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500 font-medium">
                  No violations logged yet. Active detections will automatically register here.
                </td>
              </tr>
            ) : (
              violations.map((v) => {
                const startDate = new Date(v.started_at).toLocaleString();
                const snapshotUrl = getSnapshotUrl(v.snapshot_path);

                return (
                  <tr key={v.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-4 py-3 font-mono text-slate-400">#{v.id}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1.5 text-slate-200 font-semibold">
                        <Camera className="w-3.5 h-3.5 text-sky-400" />
                        {v.camera_id}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono font-bold text-amber-400">
                      ID:{v.track_id}
                    </td>
                    <td className="px-4 py-3 text-slate-300 text-xs font-mono">
                      <div className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-slate-500" />
                        {startDate}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {v.ended_at ? (
                        <span className="px-2 py-1 rounded bg-slate-800 text-slate-400 text-xs font-mono">
                          RESOLVED
                        </span>
                      ) : (
                        <span className="px-2 py-1 rounded bg-rose-500/20 text-rose-400 text-xs font-mono font-bold animate-pulse">
                          ACTIVE VIOLATION
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {snapshotUrl ? (
                        <button
                          onClick={() => setSelectedSnapshot(snapshotUrl)}
                          className="inline-flex items-center gap-1 text-xs text-sky-400 hover:text-sky-300 underline font-medium"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          View Image
                        </button>
                      ) : (
                        <span className="text-slate-600 text-xs">No image</span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Snapshot Preview Modal */}
      {selectedSnapshot && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass-panel p-4 rounded-2xl max-w-3xl w-full">
            <div className="flex justify-between items-center mb-3">
              <h4 className="font-bold text-slate-200">Violation Snapshot Preview</h4>
              <button
                onClick={() => setSelectedSnapshot(null)}
                className="text-slate-400 hover:text-white px-2 py-1 bg-slate-800 rounded text-sm"
              >
                Close
              </button>
            </div>
            <img
              src={selectedSnapshot}
              alt="Violation Snapshot"
              className="w-full h-auto rounded-lg border border-slate-700"
            />
          </div>
        </div>
      )}
    </div>
  );
};

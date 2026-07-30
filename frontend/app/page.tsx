'use client';

import React, { useState, useEffect } from 'react';
import { Play, Square, RefreshCw, AlertCircle, Video } from 'lucide-react';
import { useLiveSocket } from '@/lib/useLiveSocket';
import { LiveCanvas } from '@/components/LiveCanvas';
import { StatsCards } from '@/components/StatsCards';
import { ViolationBanner } from '@/components/ViolationBanner';
import { TrendChart } from '@/components/TrendChart';
import { startStream, stopStream, fetchViolations, ViolationRecord } from '@/lib/api';

export default function DashboardPage() {
  const { payload, isConnected, isConnecting, error } = useLiveSocket();
  const [streamSource, setStreamSource] = useState<string>('6570562-hd_1080_1920_25fps.mp4');
  const [recentViolations, setRecentViolations] = useState<ViolationRecord[]>([]);
  const [isStartingStream, setIsStartingStream] = useState<boolean>(false);

  const loadRecentViolations = async () => {
    const records = await fetchViolations(undefined, 10);
    setRecentViolations(records);
  };

  useEffect(() => {
    loadRecentViolations();
    const interval = setInterval(loadRecentViolations, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStartStream = async () => {
    setIsStartingStream(true);
    try {
      await startStream(streamSource, 'cam-01');
    } catch (e) {
      console.error(e);
    } finally {
      setIsStartingStream(false);
    }
  };

  const handleStopStream = async () => {
    try {
      await stopStream();
    } catch (e) {
      console.error(e);
    }
  };

  const isViolationActive = (payload?.stats?.violations ?? 0) > 0;

  return (
    <div className="space-y-6">
      {/* Top Banner Alert when active violation present */}
      <ViolationBanner
        isViolationActive={isViolationActive}
        violationsCount={payload?.stats?.violations ?? 1}
      />

      {/* Real-time Stats Cards */}
      <StatsCards stats={payload?.stats} />

      {/* Main Grid Section: Video Feed + Stream Controls + Recent Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 spans): Live Video & Canvas Overlay */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between bg-slate-900/60 p-3 rounded-xl border border-slate-800">
            <div className="flex items-center space-x-3">
              <Video className="w-5 h-5 text-sky-400" />
              <span className="text-sm font-bold text-slate-200">Camera Source:</span>
              <select
                value={streamSource}
                onChange={(e) => setStreamSource(e.target.value)}
                className="bg-slate-800 border border-slate-700 text-xs text-slate-200 px-3 py-1.5 rounded-lg focus:outline-none focus:border-rose-500"
              >
                <option value="6570562-hd_1080_1920_25fps.mp4">HD Sample Video (6570562-hd_1080_1920_25fps.mp4)</option>
                <option value="0">Webcam / Primary Input (Index 0)</option>
                <option value="rtsp://192.168.1.100:554/stream">RTSP IP Camera Stream</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={handleStartStream}
                disabled={isStartingStream}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg transition disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Start</span>
              </button>
              <button
                onClick={handleStopStream}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-rose-600 text-slate-300 hover:text-white text-xs font-bold rounded-lg transition"
              >
                <Square className="w-3.5 h-3.5" />
                <span>Stop</span>
              </button>
            </div>
          </div>

          {/* Live Video Canvas Overlay */}
          <LiveCanvas payload={payload} />

          {/* System Status Connection Info */}
          <div className="flex items-center justify-between text-xs text-slate-400 px-2 font-mono">
            <span>
              WS Status:{' '}
              {isConnected ? (
                <span className="text-emerald-400 font-bold">CONNECTED</span>
              ) : isConnecting ? (
                <span className="text-amber-400 font-bold">CONNECTING...</span>
              ) : (
                <span className="text-rose-500 font-bold">DISCONNECTED</span>
              )}
            </span>
            <span>Last Packet: {payload?.timestamp ? new Date(payload.timestamp).toLocaleTimeString() : 'N/A'}</span>
          </div>
        </div>

        {/* Right Column (1 span): Trend Chart + Live Violation Feed */}
        <div className="space-y-6">
          <TrendChart />

          {/* Recent Violations Feed */}
          <div className="glass-panel p-4 rounded-xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-500" />
                <span>Live Violation Alerts</span>
              </h3>
              <button
                onClick={loadRecentViolations}
                className="text-slate-400 hover:text-white p-1 rounded transition"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {recentViolations.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-6">
                  No recent violations recorded.
                </p>
              ) : (
                recentViolations.map((vio) => (
                  <div
                    key={vio.id}
                    className="p-3 bg-slate-900/80 rounded-lg border border-slate-800 flex items-center justify-between"
                  >
                    <div>
                      <p className="text-xs font-bold text-slate-200">
                        Camera {vio.camera_id} • Track #{vio.track_id}
                      </p>
                      <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                        {new Date(vio.started_at).toLocaleTimeString()}
                      </p>
                    </div>
                    <span className="text-xs font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded">
                      CONFIRMED
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

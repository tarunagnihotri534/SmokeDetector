'use client';

import React, { useRef, useEffect } from 'react';
import { LiveFeedPayload } from '@/lib/useLiveSocket';

interface LiveCanvasProps {
  payload: LiveFeedPayload | null;
  feedUrl?: string;
  className?: string;
}

export const LiveCanvas: React.FC<LiveCanvasProps> = ({
  payload,
  feedUrl = 'http://localhost:8000/api/streams/feed',
  className = ''
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const img = imageRef.current;
    if (!canvas || !img) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Adjust canvas dimensions to match container rendered display size
    const displayWidth = img.clientWidth || 1280;
    const displayHeight = img.clientHeight || 720;
    canvas.width = displayWidth;
    canvas.height = displayHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!payload) return;

    // Dynamic coordinate space from inference payload (fallback to 1280x720)
    const srcWidth = payload?.frame_width || 1280;
    const srcHeight = payload?.frame_height || 720;

    const scaleX = displayWidth / srcWidth;
    const scaleY = displayHeight / srcHeight;

    // 1. Draw Cigarette Bounding Boxes (Orange)
    if (payload.cigarettes) {
      payload.cigarettes.forEach((cig) => {
        const [x1, y1, x2, y2] = cig.bbox;
        const sx1 = x1 * scaleX;
        const sy1 = y1 * scaleY;
        const sw = (x2 - x1) * scaleX;
        const sh = (y2 - y1) * scaleY;

        ctx.strokeStyle = '#f97316'; // Orange
        ctx.lineWidth = 2;
        ctx.strokeRect(sx1, sy1, sw, sh);

        // Label tag
        const label = `cigarette ${(cig.confidence * 100).toFixed(0)}%`;
        ctx.font = 'bold 12px sans-serif';
        const textWidth = ctx.measureText(label).width;

        ctx.fillStyle = '#f97316';
        ctx.fillRect(sx1, Math.max(0, sy1 - 18), textWidth + 8, 18);
        ctx.fillStyle = '#ffffff';
        ctx.fillText(label, sx1 + 4, Math.max(12, sy1 - 4));
      });
    }

    // 2. Draw Person Bounding Boxes (Green = Safe, Red = Violation/Smoking)
    if (payload.persons) {
      payload.persons.forEach((person) => {
        const [x1, y1, x2, y2] = person.bbox;
        const sx1 = x1 * scaleX;
        const sy1 = y1 * scaleY;
        const sw = (x2 - x1) * scaleX;
        const sh = (y2 - y1) * scaleY;

        let strokeColor = '#22c55e'; // Green (Safe)
        let statusTag = '';

        if (person.status === 'violation') {
          strokeColor = '#ef4444'; // Red (Violation)
          statusTag = ' [VIOLATION]';
        } else if (person.status === 'smoking') {
          strokeColor = '#f97316'; // Orange (Smoking debounce)
          statusTag = ' [SMOKING]';
        }

        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 3;
        ctx.strokeRect(sx1, sy1, sw, sh);

        // Header label tag
        const label = `ID:${person.track_id} person ${(person.confidence * 100).toFixed(0)}%${statusTag}`;
        ctx.font = 'bold 13px sans-serif';
        const textWidth = ctx.measureText(label).width;

        ctx.fillStyle = strokeColor;
        ctx.fillRect(sx1, Math.max(0, sy1 - 22), textWidth + 10, 22);
        ctx.fillStyle = '#ffffff';
        ctx.fillText(label, sx1 + 5, Math.max(15, sy1 - 6));
      });
    }

  }, [payload]);

  return (
    <div ref={containerRef} className={`relative rounded-xl overflow-hidden glass-panel ${className}`}>
      {/* MJPEG Live Stream Image */}
      <img
        ref={imageRef}
        src={feedUrl}
        alt="Live Camera Feed"
        className="w-full h-auto block object-cover bg-slate-950"
      />

      {/* Overlay Canvas */}
      <canvas
        ref={canvasRef}
        className="absolute top-0 left-0 w-full h-full pointer-events-none"
      />

      {/* Top Feed Status Indicator */}
      <div className="absolute top-4 left-4 flex items-center space-x-2 bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-slate-700/50 text-xs font-medium">
        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></span>
        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
        <span className="text-slate-200">LIVE FEED • {payload?.camera_id || 'cam-01'}</span>
      </div>
    </div>
  );
};

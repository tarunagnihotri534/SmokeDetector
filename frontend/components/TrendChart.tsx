'use client';

import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';

interface TrendChartProps {
  data?: { time: string; violations: number }[];
}

const mockTrendData = [
  { time: '08:00', violations: 0 },
  { time: '10:00', violations: 1 },
  { time: '12:00', violations: 3 },
  { time: '14:00', violations: 2 },
  { time: '16:00', violations: 4 },
  { time: '18:00', violations: 1 },
  { time: '20:00', violations: 5 },
];

export const TrendChart: React.FC<TrendChartProps> = ({ data = mockTrendData }) => {
  return (
    <div className="glass-panel p-5 rounded-xl">
      <h3 className="text-md font-bold text-slate-200 mb-4 flex items-center justify-between">
        <span>Violation Frequency Trend</span>
        <span className="text-xs text-slate-400 font-normal">Today (Hourly)</span>
      </h3>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorViolations" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
            <YAxis stroke="#64748b" fontSize={12} allowDecimals={false} />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
            />
            <Area
              type="monotone"
              dataKey="violations"
              stroke="#ef4444"
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#colorViolations)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

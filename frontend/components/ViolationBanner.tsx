'use client';

import React from 'react';
import { AlertOctagon } from 'lucide-react';

interface ViolationBannerProps {
  isViolationActive: boolean;
  violationsCount?: number;
}

export const ViolationBanner: React.FC<ViolationBannerProps> = ({
  isViolationActive,
  violationsCount = 1
}) => {
  if (!isViolationActive) return null;

  return (
    <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50 w-11/12 max-w-2xl">
      <div className="glass-panel-danger animate-pulse-glow px-6 py-4 rounded-2xl flex items-center justify-between text-white shadow-2xl">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-red-600 rounded-xl animate-bounce">
            <AlertOctagon className="w-8 h-8 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-extrabold tracking-wider uppercase text-white flex items-center gap-2">
              <span>SMOKER DETECTED</span>
              <span className="text-xs px-2 py-0.5 bg-red-800 rounded-full font-bold">
                {violationsCount} Active
              </span>
            </h3>
            <p className="text-sm text-red-100/90 font-medium">
              Cigarette smoking violation confirmed in active camera feed!
            </p>
          </div>
        </div>

        <div className="hidden sm:block">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-white/20 text-white border border-white/30">
            AUTO-LOGGED TO DB
          </span>
        </div>
      </div>
    </div>
  );
};

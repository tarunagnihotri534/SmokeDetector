'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ShieldAlert, Video, FileText, Camera, Radio } from 'lucide-react';

export const Navbar: React.FC = () => {
  const pathname = usePathname();

  const navLinks = [
    { href: '/', label: 'Live Dashboard', icon: Video },
    { href: '/violations', label: 'Violations History', icon: FileText },
    { href: '/cameras', label: 'Camera Manager', icon: Camera },
  ];

  return (
    <header className="sticky top-0 z-40 bg-[#090d16]/90 backdrop-blur-lg border-b border-slate-800 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand / Logo */}
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="p-2.5 bg-gradient-to-tr from-rose-600 to-amber-500 rounded-xl text-white shadow-lg shadow-rose-900/30 group-hover:scale-105 transition">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-extrabold text-lg text-slate-100 tracking-tight flex items-center gap-2">
              SmokeGuard AI
              <span className="text-[10px] px-2 py-0.5 bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-full font-mono">
                v1.0
              </span>
            </h1>
            <p className="text-xs text-slate-400 font-medium">Real-Time Cigarette Detection</p>
          </div>
        </Link>

        {/* Nav Links */}
        <nav className="flex items-center space-x-1 bg-slate-900/80 p-1.5 rounded-xl border border-slate-800">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;

            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition ${
                  isActive
                    ? 'bg-rose-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Live System Status Pill */}
        <div className="hidden md:flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300">
          <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
          <span>SYSTEM ACTIVE</span>
        </div>
      </div>
    </header>
  );
};

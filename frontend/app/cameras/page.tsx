'use client';

import React, { useState, useEffect } from 'react';
import { Camera, Plus, Trash2, Video, CheckCircle } from 'lucide-react';
import { fetchCameras, CameraRecord, startStream } from '@/lib/api';

export default function CamerasPage() {
  const [cameras, setCameras] = useState<CameraRecord[]>([]);
  const [newCamId, setNewCamId] = useState<string>('');
  const [newCamName, setNewCamName] = useState<string>('');
  const [newCamUrl, setNewCamUrl] = useState<string>('0');
  const [newCamType, setNewCamType] = useState<string>('webcam');

  const loadCameras = async () => {
    const list = await fetchCameras();
    setCameras(list);
  };

  useEffect(() => {
    loadCameras();
  }, []);

  const handleSelectCamera = async (cam: CameraRecord) => {
    try {
      await startStream(cam.source_url, cam.id);
      alert(`Switched active stream to camera: ${cam.name}`);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-panel p-6 rounded-2xl border-l-4 border-l-sky-500">
        <h2 className="text-2xl font-extrabold text-slate-100 flex items-center gap-2">
          <Camera className="w-6 h-6 text-sky-400" />
          Camera Source Management
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Configure video sources (Webcam indices, video file paths, or RTSP stream URLs).
        </p>
      </div>

      {/* Camera Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cameras.map((cam) => (
          <div key={cam.id} className="glass-panel p-5 rounded-xl space-y-3 relative group">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Video className="w-5 h-5 text-sky-400" />
                <h3 className="font-bold text-slate-100">{cam.name}</h3>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                {cam.status}
              </span>
            </div>

            <div className="text-xs text-slate-400 space-y-1 font-mono">
              <p>ID: {cam.id}</p>
              <p>Type: {cam.source_type}</p>
              <p className="truncate">URL: {cam.source_url}</p>
            </div>

            <button
              onClick={() => handleSelectCamera(cam)}
              className="w-full py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold rounded-lg transition flex items-center justify-center space-x-1.5"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Activate Feed</span>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

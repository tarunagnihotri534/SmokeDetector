'use client';

import { useState, useEffect, useRef, useCallback } from 'react';

export interface PersonDetection {
  track_id: number;
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
  status: 'safe' | 'smoking' | 'violation';
  confidence: number;
}

export interface CigaretteDetection {
  bbox: [number, number, number, number];
  confidence: number;
}

export interface StreamStats {
  total_persons: number;
  smoking: number;
  safe: number;
  violations: number;
}

export interface LiveFeedPayload {
  timestamp: string;
  camera_id: string;
  frame_width?: number;
  frame_height?: number;
  persons: PersonDetection[];
  cigarettes: CigaretteDetection[];
  stats: StreamStats;
}

export function useLiveSocket(wsUrl: string = 'ws://localhost:8000/ws/live') {
  const [payload, setPayload] = useState<LiveFeedPayload | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isConnecting, setIsConnecting] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    try {
      setIsConnecting(true);
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        console.log('[WebSocket] Connected to live feed');
      };

      ws.onmessage = (event) => {
        try {
          const data: LiveFeedPayload = JSON.parse(event.data);
          setPayload(data);
        } catch (e) {
          console.error('[WebSocket] Error parsing JSON payload:', e);
        }
      };

      ws.onerror = (evt) => {
        console.warn('[WebSocket] Connection error:', evt);
        setError('WebSocket error connecting to backend stream');
      };

      ws.onclose = () => {
        setIsConnected(false);
        setIsConnecting(false);
        console.log('[WebSocket] Connection closed. Retrying in 3s...');
        reconnectTimerRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };
    } catch (e) {
      setError('Failed to instantiate WebSocket');
      setIsConnecting(false);
    }
  }, [wsUrl]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [connect]);

  return { payload, isConnected, isConnecting, error };
}

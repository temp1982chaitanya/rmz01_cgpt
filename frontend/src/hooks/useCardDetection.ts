import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  DetectionResult,
  RummyAnalysis,
  PerformanceMetrics,
  SystemStatus
} from '../types';

export function useCardDetection() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<NodeJS.Timeout | null>(null);
  const queryClient = useQueryClient();

  const [isConnecting, setIsConnecting] = useState(false);
  const [realTimeData, setRealTimeData] = useState<{
    detection?: DetectionResult;
    analysis?: RummyAnalysis;
    performance?: PerformanceMetrics;
  }>({});

  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    isConnected: false,
    isDetecting: false,
    lastUpdate: Date.now(),
    error: null
  });

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || isConnecting) return;

    const WEBSOCKET_URI = import.meta.env.VITE_WEBSOCKET_URI;
    const ws = new WebSocket(WEBSOCKET_URI);
    wsRef.current = ws;
    setIsConnecting(true);

    ws.onopen = () => {
      console.log("✅ WebSocket connected");
      setSystemStatus(prev => ({
        ...prev,
        isConnected: true,
        error: null,
        lastUpdate: Date.now()
      }));
      setIsConnecting(false);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        console.log("📨 Message received:", msg.type);

        if (msg.type === 'detection' && msg.payload?.framePreview) {
          console.log("🖼️ Frame preview detected");
          setRealTimeData(prev => ({ ...prev, detection: msg.payload }));
          setSystemStatus(prev => ({ ...prev, lastUpdate: Date.now() }));
          queryClient.invalidateQueries({ queryKey: ['detection-results'] });
        }

        if (msg.type === 'strategy' && msg.payload?.suggestions) {
          setRealTimeData(prev => ({ ...prev, analysis: msg.payload }));
          queryClient.invalidateQueries({ queryKey: ['rummy-analysis'] });
        }

        if (msg.type === 'performance' && msg.payload?.fps !== undefined) {
          setRealTimeData(prev => ({ ...prev, performance: msg.payload }));
          queryClient.invalidateQueries({ queryKey: ['performance-metrics'] });
        }

      } catch (err) {
        console.error("❌ Invalid WebSocket message", err);
      }
    };

    ws.onerror = (err) => {
      console.error("❌ WebSocket error", err);
      setSystemStatus(prev => ({
        ...prev,
        isConnected: false,
        error: 'WebSocket connection error'
      }));
      setIsConnecting(false);
    };

    ws.onclose = () => {
      console.warn("🔌 WebSocket closed");
      setSystemStatus(prev => ({
        ...prev,
        isConnected: false,
        error: 'WebSocket disconnected'
      }));
      reconnectRef.current = setTimeout(connectWebSocket, 4000);
    };
  }, [isConnecting, queryClient]);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };
  }, [connectWebSocket]);

  const startDetection = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command: 'start' }));
      console.log("📤 Sent 'start' command");
      setSystemStatus(prev => ({ ...prev, isDetecting: true }));
    }
  }, []);

  const stopDetection = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command: 'stop' }));
      console.log("📤 Sent 'stop' command");
      setSystemStatus(prev => ({ ...prev, isDetecting: false }));
    }
  }, []);

  const saveSnapshot = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command: 'save_snapshot' }));
      console.log("📤 Sent 'save_snapshot' command");
    }
  }, []);

  const detectionQuery = useQuery({
    queryKey: ['detection-results'],
    queryFn: async (): Promise<DetectionResult> =>
      realTimeData.detection || {
        handCards: [],
        discardedCard: null,
        gameJoker: null,
        overlaps: [],
        timestamp: Date.now(),
        framePreview: null
      },
    enabled: systemStatus.isDetecting,
    refetchInterval: 1000
  });

  const analysisQuery = useQuery({
    queryKey: ['rummy-analysis'],
    queryFn: async (): Promise<RummyAnalysis> =>
      realTimeData.analysis || {
        sequences: [],
        sets: [],
        suggestions: [],
        completionPercentage: 0,
        canDeclare: false
      },
    enabled: systemStatus.isDetecting,
    refetchInterval: 2000
  });

  const performanceQuery = useQuery({
    queryKey: ['performance-metrics'],
    queryFn: async (): Promise<PerformanceMetrics> =>
      realTimeData.performance || {
        fps: 0,
        avgConfidence: 0,
        detectionRate: 0,
        overlapsDetected: 0,
        totalFrames: 0
      },
    enabled: systemStatus.isDetecting,
    refetchInterval: 1000
  });

  const isWebSocketReady = wsRef.current?.readyState === WebSocket.OPEN;
  const framePreview = detectionQuery.data?.framePreview || null;

  return {
    detectionResult: detectionQuery.data,
    rummyAnalysis: analysisQuery.data,
    performanceMetrics: performanceQuery.data,
    systemStatus,
    isWebSocketReady,
    isLoading: isConnecting || detectionQuery.isLoading || analysisQuery.isLoading || performanceQuery.isLoading,
    framePreview,
    startDetection,
    stopDetection,
    saveSnapshot,
    reconnect: connectWebSocket
  };
}
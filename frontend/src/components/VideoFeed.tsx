import React, { useRef, useEffect, useState } from 'react';
import { Camera, Upload, Play, Square, RefreshCw } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { DetectionResult } from '../types';

interface VideoFeedProps {
  detectionResult: DetectionResult | undefined;
  isDetecting: boolean;
  onStartDetection: () => void;
  onStopDetection: () => void;
  onUploadImage: (file: File) => Promise<{ success: boolean; message: string }>;
}

export function VideoFeed({
  detectionResult,
  isDetecting,
  onStartDetection,
  onStopDetection,
  onUploadImage
}: VideoFeedProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [selectedCamera] = useState('ADB Mobile Screen');

  useEffect(() => {
    if (detectionResult && canvasRef.current) {
      drawDetectionOverlay(detectionResult);
    }
  }, [detectionResult]);

  const drawDetectionOverlay = (result: DetectionResult) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    result.handCards.forEach((card, index) => {
      const x = (index % 7) * 110 + 20;
      const y = Math.floor(index / 7) * 100 + 50;

      ctx.fillStyle = card.hasOverlap ? '#ef4444' : '#3b82f6';
      ctx.fillRect(x, y, 90, 120);

      ctx.strokeStyle = card.hasOverlap ? '#dc2626' : '#1d4ed8';
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, 90, 120);

      ctx.fillStyle = '#ffffff';
      ctx.font = '14px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(`${card.rank}${card.suit}`, x + 45, y + 65);

      ctx.font = '10px Arial';
      ctx.fillText(`${(card.confidence * 100).toFixed(0)}%`, x + 45, y + 85);
    });

    if (result.discardedCard) {
      const card = result.discardedCard;
      ctx.fillStyle = '#f59e0b';
      ctx.fillRect(350, 250, 90, 120);
      ctx.strokeStyle = '#d97706';
      ctx.lineWidth = 2;
      ctx.strokeRect(350, 250, 90, 120);
      ctx.fillStyle = '#ffffff';
      ctx.font = '14px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(`${card.rank}${card.suit.charAt(0).toUpperCase()}`, 395, 315);
      ctx.font = '10px Arial';
      ctx.fillText('Discarded', 395, 285);
    }

    if (result.gameJoker) {
      const card = result.gameJoker;
      ctx.fillStyle = '#8b5cf6';
      ctx.fillRect(480, 250, 90, 120);
      ctx.strokeStyle = '#7c3aed';
      ctx.lineWidth = 2;
      ctx.strokeRect(480, 250, 90, 120);
      ctx.fillStyle = '#ffffff';
      ctx.font = '14px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(`${card.rank}${card.suit.charAt(0).toUpperCase()}`, 525, 315);
      ctx.font = '10px Arial';
      ctx.fillText('Joker', 525, 285);
    }

    ctx.fillStyle = '#10b981';
    ctx.font = '16px Arial';
    ctx.textAlign = 'left';
    ctx.fillText(`Cards Detected: ${result.handCards.length}/13`, 20, 30);
    ctx.fillText(`Overlaps: ${result.overlaps.length}`, 250, 30);
    ctx.fillText(`Status: ${isDetecting ? 'Detecting' : 'Paused'}`, 400, 30);
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadStatus('Uploading...');
    try {
      const result = await onUploadImage(file);
      setUploadStatus(result.success ? 'Upload successful' : result.message);
      setTimeout(() => setUploadStatus(null), 3000);
    } catch {
      setUploadStatus('Upload failed');
      setTimeout(() => setUploadStatus(null), 3000);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Camera className="h-5 w-5" />
              Live Video Feed
            </CardTitle>
            <CardDescription>
              Real-time mobile screen capture with overlay cognition
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={isDetecting ? 'default' : 'secondary'}>
              {isDetecting ? 'Active' : 'Paused'}
            </Badge>
            <Badge variant="outline">{selectedCamera}</Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            onClick={isDetecting ? onStopDetection : onStartDetection}
            variant={isDetecting ? 'destructive' : 'default'}
            size="sm"
          >
            {isDetecting ? (
              <>
                <Square className="h-4 w-4 mr-2" />
                Stop Detection
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Start Detection
              </>
            )}
          </Button>

          <Button
            onClick={() => fileInputRef.current?.click()}
            variant="outline"
            size="sm"
          >
            <Upload className="h-4 w-4 mr-2" />
            Upload Image
          </Button>

          <Button
            onClick={() => {
              if (isDetecting) {
                onStopDetection();
                setTimeout(onStartDetection, 150);
              }
            }}
            variant="outline"
            size="sm"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>

          {uploadStatus && (
            <Badge variant={uploadStatus.includes('success') ? 'default' : 'destructive'}>
              {uploadStatus}
            </Badge>
          )}
        </div>

        <div className="relative border rounded-lg overflow-hidden bg-gray-900">
          <canvas
            ref={canvasRef}
            width={800}
            height={400}
            className="w-full h-auto"
          />

          {/* ✅ Frame preview rendering */}
          {detectionResult?.framePreview && (
            <img
              src={`data:image/jpeg;base64,${detectionResult.framePreview}`}
              alt="Frame Preview"
              className="absolute top-0 left-0 w-full h-full object-cover opacity-25 pointer-events-none"
            />
          )}

          {/* 🧪 Fallback if framePreview is missing */}
          {!detectionResult?.framePreview && (
            <div className="absolute inset-0 flex items-center justify-center text-white text-sm">
              <p>No frame preview received</p>
            </div>
          )}

          {!isDetecting && (
            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
              <div className="text-white text-center">
                <Camera className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p className="text-lg font-medium">Detection Paused</p>
                <p className="text-sm opacity-75">Click Start to begin</p>
              </div>
            </div>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileUpload}
          className="hidden"
        />
      </CardContent>
    </Card>
  );
}
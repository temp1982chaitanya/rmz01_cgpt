import React from 'react'
import { Activity, Zap, Target, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { PerformanceMetrics, SystemStatus } from '../types'
import { formatFPS, formatConfidence } from '../lib/utils'

interface PerformanceMonitorProps {
  metrics: PerformanceMetrics | undefined
  systemStatus: SystemStatus
  isLoading: boolean
}

export function PerformanceMonitor({ metrics, systemStatus, isLoading }: PerformanceMonitorProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Performance Monitor
          </CardTitle>
          <CardDescription>Loading performance data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="animate-pulse bg-gray-200 h-4 rounded"></div>
            <div className="animate-pulse bg-gray-200 h-4 rounded w-3/4"></div>
            <div className="animate-pulse bg-gray-200 h-4 rounded w-1/2"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const getStatusColor = (status: SystemStatus) => {
    if (status.error) return 'destructive'
    if (!status.isConnected) return 'secondary'
    if (status.isDetecting) return 'default'
    return 'secondary'
  }

  const getStatusText = (status: SystemStatus) => {
    if (status.error) return 'Error'
    if (!status.isConnected) return 'Disconnected'
    if (status.isDetecting) return 'Active'
    return 'Standby'
  }

  const getFPSColor = (fps: number) => {
    if (fps >= 0.7) return 'text-green-500'
    if (fps >= 0.5) return 'text-yellow-500'
    return 'text-red-500'
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-500'
    if (confidence >= 0.6) return 'text-yellow-500'
    return 'text-red-500'
  }

  return (
    <div className="space-y-4">
      {/* System Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            System Status
          </CardTitle>
          <CardDescription>
            Current system connection and detection status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Status</span>
              <Badge variant={getStatusColor(systemStatus)}>
                {getStatusText(systemStatus)}
              </Badge>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Connection</span>
              <Badge variant={systemStatus.isConnected ? "default" : "secondary"}>
                {systemStatus.isConnected ? "Connected" : "Disconnected"}
              </Badge>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Detection</span>
              <Badge variant={systemStatus.isDetecting ? "default" : "secondary"}>
                {systemStatus.isDetecting ? "Running" : "Stopped"}
              </Badge>
            </div>
            
            {systemStatus.error && (
              <div className="flex items-start gap-2 p-2 bg-red-50 rounded-lg border border-red-200">
                <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-red-800">{systemStatus.error}</span>
              </div>
            )}
            
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Last Update</span>
              <span>
                {new Date(systemStatus.lastUpdate).toLocaleTimeString()}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      {metrics && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Performance Metrics
            </CardTitle>
            <CardDescription>
              Real-time detection performance statistics
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">FPS</span>
                  <span className={`text-sm font-bold ${getFPSColor(metrics.fps)}`}>
                    {formatFPS(metrics.fps)}
                  </span>
                </div>
                <div className="text-xs text-gray-500">Frames per second</div>
              </div>
              
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Avg Confidence</span>
                  <span className={`text-sm font-bold ${getConfidenceColor(metrics.avgConfidence)}`}>
                    {formatConfidence(metrics.avgConfidence)}
                  </span>
                </div>
                <div className="text-xs text-gray-500">Detection accuracy</div>
              </div>
              
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Detection Rate</span>
                  <span className="text-sm font-bold text-green-500">
                    {metrics.detectionRate}%
                  </span>
                </div>
                <div className="text-xs text-gray-500">Success rate</div>
              </div>
              
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Overlaps</span>
                  <span className={`text-sm font-bold ${
                    metrics.overlapsDetected > 0 ? 'text-red-500' : 'text-green-500'
                  }`}>
                    {metrics.overlapsDetected}
                  </span>
                </div>
                <div className="text-xs text-gray-500">Card overlaps</div>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Total Frames</span>
                <span className="text-sm font-bold text-blue-500">
                  {metrics.totalFrames.toLocaleString()}
                </span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Processed since session start
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Detection History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Detection History
          </CardTitle>
          <CardDescription>
            Recent detection events and statistics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-green-50 rounded border border-green-200">
              <span className="text-sm">Hand cards detected</span>
              <Badge variant="outline">13/13</Badge>
            </div>
            <div className="flex items-center justify-between p-2 bg-blue-50 rounded border border-blue-200">
              <span className="text-sm">Sequences identified</span>
              <Badge variant="outline">2 found</Badge>
            </div>
            <div className="flex items-center justify-between p-2 bg-purple-50 rounded border border-purple-200">
              <span className="text-sm">Sets identified</span>
              <Badge variant="outline">1 found</Badge>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 rounded border border-gray-200">
              <span className="text-sm">Last joker update</span>
              <Badge variant="outline">2s ago</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
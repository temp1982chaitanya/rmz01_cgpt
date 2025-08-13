import React from 'react'
import { Target, TrendingUp, AlertTriangle, CheckCircle, Zap } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Progress } from './ui/progress'
import { RummyAnalysis } from '../types'
import { formatConfidence } from '../lib/utils'

interface CardAnalysisProps {
  analysis: RummyAnalysis | undefined
  isLoading: boolean
}

export function CardAnalysis({ analysis, isLoading }: CardAnalysisProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Rummy Analysis
          </CardTitle>
          <CardDescription>Analyzing hand composition...</CardDescription>
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

  if (!analysis) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Rummy Analysis
          </CardTitle>
          <CardDescription>No analysis data available</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            <Target className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>Start detection to see analysis</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const getSuitSymbol = (suit: string) => {
    const symbols = {
      hearts: '♥',
      diamonds: '♦',
      clubs: '♣',
      spades: '♠'
    }
    return symbols[suit as keyof typeof symbols] || suit
  }

  const getCompletionColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-500'
    if (percentage >= 60) return 'text-yellow-500'
    return 'text-red-500'
  }

  return (
    <div className="space-y-4">
      {/* Completion Progress */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Game Progress
          </CardTitle>
          <CardDescription>
            Current hand completion status
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Completion</span>
            <span className={`text-sm font-bold ${getCompletionColor(analysis.completionPercentage)}`}>
              {analysis.completionPercentage}%
            </span>
          </div>
          <Progress value={analysis.completionPercentage} className="h-2" />
          
          <div className="flex items-center justify-between">
            <Badge variant={analysis.canDeclare ? "default" : "secondary"}>
              {analysis.canDeclare ? "Can Declare" : "Cannot Declare"}
            </Badge>
            {analysis.canDeclare && (
              <CheckCircle className="h-5 w-5 text-green-500" />
            )}
          </div>
        </CardContent>
      </Card>

      {/* Sequences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Sequences ({analysis.sequences.length})
          </CardTitle>
          <CardDescription>
            Detected sequences in your hand
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {analysis.sequences.length === 0 ? (
              <div className="text-center py-4 text-gray-500">
                <AlertTriangle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No sequences detected</p>
              </div>
            ) : (
              analysis.sequences.map((sequence, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg border ${
                    sequence.isValid ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant={sequence.type === 'pure' ? 'default' : 'secondary'}>
                      {sequence.type === 'pure' ? 'Pure Sequence' : 'Joker Sequence'}
                    </Badge>
                    {sequence.isValid && <CheckCircle className="h-4 w-4 text-green-500" />}
                  </div>
                  <div className="flex items-center gap-2">
                    {sequence.cards.map((card, cardIndex) => (
                      <div
                        key={cardIndex}
                        className="flex items-center gap-1 bg-white px-2 py-1 rounded border"
                      >
                        <span className="font-medium">{card.rank}</span>
                        <span className={`text-sm ${
                          card.suit === 'hearts' || card.suit === 'diamonds' 
                            ? 'text-red-500' 
                            : 'text-gray-700'
                        }`}>
                          {getSuitSymbol(card.suit)}
                        </span>
                        <span className="text-xs text-gray-500">
                          {formatConfidence(card.confidence)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Sets */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Sets ({analysis.sets.length})
          </CardTitle>
          <CardDescription>
            Detected sets in your hand
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {analysis.sets.length === 0 ? (
              <div className="text-center py-4 text-gray-500">
                <AlertTriangle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No sets detected</p>
              </div>
            ) : (
              analysis.sets.map((set, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg border ${
                    set.isValid ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline">Set</Badge>
                    {set.isValid && <CheckCircle className="h-4 w-4 text-green-500" />}
                  </div>
                  <div className="flex items-center gap-2">
                    {set.cards.map((card, cardIndex) => (
                      <div
                        key={cardIndex}
                        className="flex items-center gap-1 bg-white px-2 py-1 rounded border"
                      >
                        <span className="font-medium">{card.rank}</span>
                        <span className={`text-sm ${
                          card.suit === 'hearts' || card.suit === 'diamonds' 
                            ? 'text-red-500' 
                            : 'text-gray-700'
                        }`}>
                          {getSuitSymbol(card.suit)}
                        </span>
                        <span className="text-xs text-gray-500">
                          {formatConfidence(card.confidence)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Suggestions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Strategic Suggestions
          </CardTitle>
          <CardDescription>
            AI-powered gameplay recommendations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {analysis.suggestions.length === 0 ? (
              <div className="text-center py-4 text-gray-500">
                <p>No suggestions available</p>
              </div>
            ) : (
              analysis.suggestions.map((suggestion, index) => (
                <div
                  key={index}
                  className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg border border-blue-200"
                >
                  <Zap className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-blue-800">{suggestion}</p>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
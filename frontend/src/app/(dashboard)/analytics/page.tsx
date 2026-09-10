"use client"

import React, { useEffect, useState } from "react"
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  Activity,
  Target,
  Loader2,
} from "lucide-react"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import api from "@/lib/api"
import type { AnalyticsSnapshot } from "@/types"

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSnapshot | null>(null)
  const [skillsDemand, setSkillsDemand] = useState<any[]>([])
  const [jobMarket, setJobMarket] = useState<any>(null)
  const [skillCoverage, setSkillCoverage] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    async function fetchData() {
      try {
        const [summaryData, skills, market, coverage] = await Promise.allSettled([
          api.getDashboardSummary(),
          api.getSkillsDemand(),
          api.getJobMarket(),
          api.getSkillCoverage(),
        ])

        if (summaryData.status === "fulfilled") setSummary(summaryData.value)
        if (skills.status === "fulfilled") setSkillsDemand(skills.value)
        if (market.status === "fulfilled") setJobMarket(market.value)
        if (coverage.status === "fulfilled") setSkillCoverage(coverage.value)
      } catch (err: any) {
        setError(err?.message || "Failed to load analytics")
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </DashboardLayout>
    )
  }

  const overviewStats = [
    {
      title: "Application Rate",
      value: summary ? `${summary.applications_this_week}/week` : "0",
      trend: "up" as const,
      description: "Applications this week",
    },
    {
      title: "Response Rate",
      value: summary ? `${summary.response_rate}%` : "0%",
      trend: summary && summary.response_rate > 0 ? "up" as const : "down" as const,
      description: "Employer responses",
    },
    {
      title: "Interview Rate",
      value: summary ? `${summary.interview_rate}%` : "0%",
      trend: summary && summary.interview_rate > 0 ? "up" as const : "down" as const,
      description: "Interviews per application",
    },
    {
      title: "Offer Rate",
      value: summary ? `${summary.offer_rate}%` : "0%",
      trend: summary && summary.offer_rate > 0 ? "up" as const : "down" as const,
      description: "Offers per interview",
    },
  ]

  const pipelineData = jobMarket?.pipeline || []
  const maxPipeline = Math.max(...pipelineData.map((s: any) => s.count || 0), 1)

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <div>
          <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground">
            Insights into your job search performance
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {overviewStats.map((stat) => (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                {stat.trend === "up" ? (
                  <TrendingUp className="h-4 w-4 text-green-500" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-500" />
                )}
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">
                  {stat.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5" />
                Application Status Distribution
              </CardTitle>
              <CardDescription>Current status of all applications</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {pipelineData.length > 0 ? (
                  pipelineData.map((status: any) => (
                    <div key={status.stage} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span>{status.stage}</span>
                        <span className="font-medium">{status.count}</span>
                      </div>
                      <div className="h-2 rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full rounded-full bg-primary"
                          style={{ width: `${(status.count / maxPipeline) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No pipeline data available
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Skills in Demand
              </CardTitle>
              <CardDescription>Market demand vs your proficiency</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {skillsDemand.length > 0 ? (
                  skillsDemand.slice(0, 8).map((skill: any) => (
                    <div key={skill.name || skill.skill} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <span>{skill.name || skill.skill}</span>
                          {skill.your_level && (
                            <Badge variant="outline" className="text-xs capitalize">
                              {skill.your_level}
                            </Badge>
                          )}
                        </div>
                        <span className="text-muted-foreground">
                          {skill.demand ?? skill.count ?? 0}%
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full rounded-full bg-primary"
                          style={{ width: `${skill.demand ?? skill.count ?? 0}%` }}
                        />
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No skills data available
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          {skillCoverage && (
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Skill Coverage
                </CardTitle>
                <CardDescription>Your skill coverage across job requirements</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-primary">
                      {skillCoverage.coverage_percentage ?? 0}%
                    </div>
                    <p className="text-sm text-muted-foreground">Overall Coverage</p>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">
                      {skillCoverage.matching_skills ?? 0}
                    </div>
                    <p className="text-sm text-muted-foreground">Matching Skills</p>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-amber-600">
                      {skillCoverage.missing_skills ?? 0}
                    </div>
                    <p className="text-sm text-muted-foreground">Skills to Learn</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}

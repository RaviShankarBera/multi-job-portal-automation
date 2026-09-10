"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import {
  Briefcase,
  Send,
  Phone,
  Gift,
  TrendingUp,
  ArrowRight,
  Clock,
  MapPin,
  Building2,
  Loader2,
} from "lucide-react"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import api from "@/lib/api"
import type { AnalyticsSnapshot, Job, Application } from "@/types"

export default function DashboardPage() {
  const [summary, setSummary] = useState<AnalyticsSnapshot | null>(null)
  const [recommendedJobs, setRecommendedJobs] = useState<Job[]>([])
  const [pipeline, setPipeline] = useState<any>(null)
  const [followUps, setFollowUps] = useState<any[]>([])
  const [skillsDemand, setSkillsDemand] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    async function fetchData() {
      try {
        const [summaryData, jobs, pipelineData, followUpData, skills] = await Promise.allSettled([
          api.getDashboardSummary(),
          api.getJobs(0, 5),
          api.getPipeline(),
          api.getFollowUps(),
          api.getSkillsDemand(),
        ])

        if (summaryData.status === "fulfilled") setSummary(summaryData.value)
        if (jobs.status === "fulfilled") setRecommendedJobs(jobs.value)
        if (pipelineData.status === "fulfilled") setPipeline(pipelineData.value)
        if (followUpData.status === "fulfilled") setFollowUps(followUpData.value)
        if (skills.status === "fulfilled") setSkillsDemand(skills.value)
      } catch (err: any) {
        setError(err?.message || "Failed to load dashboard data")
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

  const stats = [
    {
      title: "Jobs Found",
      value: summary?.total_jobs_found ?? 0,
      icon: Briefcase,
      color: "text-blue-600 bg-blue-100 dark:bg-blue-900/50",
    },
    {
      title: "Applications",
      value: summary?.total_applications ?? 0,
      icon: Send,
      color: "text-green-600 bg-green-100 dark:bg-green-900/50",
    },
    {
      title: "Interviews",
      value: summary?.total_interviews ?? 0,
      icon: Phone,
      color: "text-purple-600 bg-purple-100 dark:bg-purple-900/50",
    },
    {
      title: "Offers",
      value: summary?.total_offers ?? 0,
      icon: Gift,
      color: "text-amber-600 bg-amber-100 dark:bg-amber-900/50",
    },
  ]

  const pipelineStages = pipeline
    ? [
        { stage: "Saved", count: pipeline.saved || 0, color: "bg-gray-500" },
        { stage: "Applied", count: pipeline.applied || 0, color: "bg-blue-500" },
        { stage: "Screening", count: pipeline.screening || 0, color: "bg-yellow-500" },
        { stage: "Interview", count: pipeline.interview || 0, color: "bg-purple-500" },
        { stage: "Offer", count: pipeline.offer || 0, color: "bg-green-500" },
      ]
    : []

  const maxPipeline = Math.max(...pipelineStages.map((s: any) => s.count), 1)

  const topSkills = skillsDemand.slice(0, 5)

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here&apos;s an overview of your job search activity.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <div className={`rounded-lg p-2 ${stat.color}`}>
                  <stat.icon className="h-4 w-4" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">
                  {stat.title === "Jobs Found" && "Total matched"}
                  {stat.title === "Applications" && `${summary?.applications_this_month ?? 0} this month`}
                  {stat.title === "Interviews" && `${summary?.interview_rate ?? 0}% rate`}
                  {stat.title === "Offers" && `${summary?.offer_rate ?? 0}% rate`}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Recommended Jobs</CardTitle>
                <CardDescription>
                  Jobs matched based on your profile and preferences
                </CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/jobs">
                  View all
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recommendedJobs.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No jobs found. Update your profile to get recommendations.
                  </p>
                )}
                {recommendedJobs.map((job) => (
                  <div
                    key={job.id}
                    className="flex items-center justify-between rounded-lg border p-4 hover:bg-muted/50 transition-colors"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium">{job.title}</h4>
                        {job.match_score != null && (
                          <Badge variant="info" className="text-xs">
                            {job.match_score}% match
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Building2 className="h-3 w-3" />
                          {job.company}
                        </span>
                        {job.location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            {job.location}
                          </span>
                        )}
                        {job.posted_date && (
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {new Date(job.posted_date).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      {job.salary_min != null && job.salary_max != null && (
                        <p className="text-sm font-medium text-primary">
                          ${job.salary_min.toLocaleString()} - ${job.salary_max.toLocaleString()}
                        </p>
                      )}
                    </div>
                    <Button size="sm" variant="outline" asChild>
                      <Link href={`/jobs/${job.id}`}>View</Link>
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Application Pipeline</CardTitle>
                <CardDescription>Track your application progress</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {pipelineStages.map((stage: any) => (
                    <div key={stage.stage} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span>{stage.stage}</span>
                        <span className="font-medium">{stage.count}</span>
                      </div>
                      <div className="h-2 rounded-full bg-muted overflow-hidden">
                        <div
                          className={`h-full rounded-full ${stage.color}`}
                          style={{ width: `${(stage.count / maxPipeline) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                  {pipelineStages.length === 0 && (
                    <p className="text-sm text-muted-foreground text-center">
                      No pipeline data yet
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Top Skills in Demand</CardTitle>
                <CardDescription>Skills employers are looking for</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {topSkills.map((skill: any) => (
                    <div key={skill.name || skill.skill} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span>{skill.name || skill.skill}</span>
                        <span className="text-muted-foreground">{skill.demand ?? skill.count ?? 0}%</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full rounded-full bg-primary"
                          style={{ width: `${skill.demand ?? skill.count ?? 0}%` }}
                        />
                      </div>
                    </div>
                  ))}
                  {topSkills.length === 0 && (
                    <p className="text-sm text-muted-foreground text-center">
                      No skills data yet
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            {followUps.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Follow-ups Due</CardTitle>
                  <CardDescription>Applications needing attention</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {followUps.slice(0, 5).map((fu: any) => (
                      <div key={fu.id} className="flex items-center justify-between text-sm">
                        <span className="truncate">{fu.job_title || `Application #${fu.id}`}</span>
                        <Badge variant="warning" className="text-xs">
                          {fu.follow_up_date}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}

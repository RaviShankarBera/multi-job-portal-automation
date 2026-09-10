"use client"

import React, { useState, useEffect, useCallback } from "react"
import Link from "next/link"
import {
  Search,
  MapPin,
  Building2,
  Clock,
  DollarSign,
  Bookmark,
  BookmarkCheck,
  SlidersHorizontal,
  Loader2,
} from "lucide-react"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import api from "@/lib/api"
import type { Job, JobSearchParams } from "@/types"

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  const [location, setLocation] = useState("")
  const [jobType, setJobType] = useState("")
  const [showFilters, setShowFilters] = useState(false)

  const fetchJobs = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const params: JobSearchParams = {
        skip: 0,
        limit: 50,
      }
      if (searchQuery) params.query = searchQuery
      if (location) params.location = location
      if (jobType) params.job_type = jobType

      const results = await api.searchJobs(params)
      setJobs(results)
    } catch (err: any) {
      setError(err?.message || "Failed to search jobs")
    } finally {
      setLoading(false)
    }
  }, [searchQuery, location, jobType])

  useEffect(() => {
    fetchJobs()
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    fetchJobs()
  }

  const toggleSave = async (job: Job) => {
    try {
      if (job.is_saved) {
        await api.unsaveJob(job.id)
        setJobs(jobs.map((j) => (j.id === job.id ? { ...j, is_saved: false } : j)))
      } else {
        await api.saveJob(job.id)
        setJobs(jobs.map((j) => (j.id === job.id ? { ...j, is_saved: true } : j)))
      }
    } catch (err: any) {
      setError(err?.message || "Failed to update save status")
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Jobs</h1>
            <p className="text-muted-foreground">
              Discover and apply to jobs that match your skills
            </p>
          </div>
          <div className="text-sm text-muted-foreground">
            {jobs.length} jobs found
          </div>
        </div>

        <form onSubmit={handleSearch} className="flex flex-col gap-4 md:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search jobs by title, company, or keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <div className="relative flex-1 md:max-w-xs">
            <MapPin className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            className="md:w-auto"
          >
            <SlidersHorizontal className="mr-2 h-4 w-4" />
            Filters
          </Button>
          <Button type="submit">Search</Button>
        </form>

        {showFilters && (
          <Card>
            <CardContent className="p-4">
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <Label>Job Type</Label>
                  <select
                    value={jobType}
                    onChange={(e) => setJobType(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="">All Types</option>
                    <option value="full-time">Full-time</option>
                    <option value="part-time">Part-time</option>
                    <option value="contract">Contract</option>
                    <option value="remote">Remote</option>
                    <option value="internship">Internship</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {!loading && (
          <div className="space-y-4">
            {jobs.map((job) => (
              <Card key={job.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-semibold">{job.title}</h3>
                        {job.match_score != null && (
                          <Badge variant="info" className="text-xs">
                            {job.match_score}% match
                          </Badge>
                        )}
                        {job.job_type && (
                          <Badge variant="outline" className="text-xs capitalize">
                            {job.job_type}
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Building2 className="h-4 w-4" />
                          {job.company}
                        </span>
                        {job.location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="h-4 w-4" />
                            {job.location}
                          </span>
                        )}
                        {job.salary_min != null && job.salary_max != null && (
                          <span className="flex items-center gap-1">
                            <DollarSign className="h-4 w-4" />
                            ${job.salary_min.toLocaleString()} - ${job.salary_max.toLocaleString()}
                          </span>
                        )}
                        {job.posted_date && (
                          <span className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            {new Date(job.posted_date).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => toggleSave(job)}
                      >
                        {job.is_saved ? (
                          <BookmarkCheck className="h-5 w-5 text-primary" />
                        ) : (
                          <Bookmark className="h-5 w-5" />
                        )}
                      </Button>
                      <Button asChild>
                        <Link href={`/jobs/${job.id}`}>View Details</Link>
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {!loading && jobs.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Search className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium">No jobs found</h3>
              <p className="text-sm text-muted-foreground">
                Try adjusting your search or filters
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}

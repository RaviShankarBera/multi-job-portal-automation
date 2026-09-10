"use client"

import React, { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import {
  ArrowLeft,
  Building2,
  MapPin,
  DollarSign,
  Clock,
  ExternalLink,
  Bookmark,
  BookmarkCheck,
  Send,
  Sparkles,
  FileText,
  Loader2,
} from "lucide-react"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import api from "@/lib/api"
import type { Job, Resume } from "@/types"

export default function JobDetailPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = Number(params.id)

  const [job, setJob] = useState<Job | null>(null)
  const [resumes, setResumes] = useState<Resume[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [applying, setApplying] = useState(false)
  const [tailoring, setTailoring] = useState(false)
  const [generatingLetter, setGeneratingLetter] = useState(false)
  const [coverLetter, setCoverLetter] = useState<string | null>(null)
  const [applied, setApplied] = useState(false)

  useEffect(() => {
    async function fetchJob() {
      try {
        const [jobData, resumesData] = await Promise.all([
          api.getJob(jobId),
          api.getResumes(),
        ])
        setJob(jobData)
        setResumes(resumesData)
      } catch (err: any) {
        setError(err?.message || "Failed to load job details")
      } finally {
        setLoading(false)
      }
    }
    if (jobId) fetchJob()
  }, [jobId])

  const handleSave = async () => {
    if (!job) return
    try {
      if (job.is_saved) {
        await api.unsaveJob(job.id)
        setJob({ ...job, is_saved: false })
      } else {
        await api.saveJob(job.id)
        setJob({ ...job, is_saved: true })
      }
    } catch (err: any) {
      setError(err?.message || "Failed to update save status")
    }
  }

  const handleApply = async () => {
    if (!job) return
    setApplying(true)
    setError("")
    try {
      const primaryResume = resumes.find((r) => r.is_primary)
      await api.createApplication({
        job_id: job.id,
        resume_id: primaryResume?.id,
      })
      setApplied(true)
    } catch (err: any) {
      setError(err?.message || "Failed to apply")
    } finally {
      setApplying(false)
    }
  }

  const handleTailorResume = async () => {
    if (!job || resumes.length === 0) return
    setTailoring(true)
    setError("")
    try {
      const primaryResume = resumes.find((r) => r.is_primary) || resumes[0]
      const result = await api.tailorResume(primaryResume.id, job.id)
      alert("Resume tailored successfully! Check your resumes page.")
    } catch (err: any) {
      setError(err?.message || "Failed to tailor resume")
    } finally {
      setTailoring(false)
    }
  }

  const handleGenerateCoverLetter = async () => {
    if (!job || resumes.length === 0) return
    setGeneratingLetter(true)
    setError("")
    try {
      const primaryResume = resumes.find((r) => r.is_primary) || resumes[0]
      const result = await api.generateCoverLetter(primaryResume.id, job.id)
      setCoverLetter(result.cover_letter || result.content || JSON.stringify(result))
    } catch (err: any) {
      setError(err?.message || "Failed to generate cover letter")
    } finally {
      setGeneratingLetter(false)
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </DashboardLayout>
    )
  }

  if (!job) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center min-h-[60vh]">
          <h2 className="text-xl font-semibold mb-2">Job not found</h2>
          <Button asChild variant="outline">
            <Link href="/jobs">Back to Jobs</Link>
          </Button>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex-1">
            <h1 className="text-2xl font-bold tracking-tight">{job.title}</h1>
            <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
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
              {job.posted_date && (
                <span className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  Posted {new Date(job.posted_date).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={handleSave}>
              {job.is_saved ? (
                <>
                  <BookmarkCheck className="mr-2 h-4 w-4" />
                  Saved
                </>
              ) : (
                <>
                  <Bookmark className="mr-2 h-4 w-4" />
                  Save
                </>
              )}
            </Button>
            <Button onClick={handleApply} disabled={applying || applied}>
              {applying ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : applied ? null : (
                <Send className="mr-2 h-4 w-4" />
              )}
              {applied ? "Applied" : applying ? "Applying..." : "Apply Now"}
            </Button>
          </div>
        </div>

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Job Description</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  {job.description ? (
                    <div className="whitespace-pre-wrap">{job.description}</div>
                  ) : (
                    <p className="text-muted-foreground">No description available</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {job.requirements && (
              <Card>
                <CardHeader>
                  <CardTitle>Requirements</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="whitespace-pre-wrap text-sm">{job.requirements}</div>
                </CardContent>
              </Card>
            )}
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Job Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Type</span>
                  <Badge variant="outline" className="capitalize">{job.job_type || "Not specified"}</Badge>
                </div>
                {job.salary_min != null && job.salary_max != null && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Salary</span>
                    <span className="text-sm font-medium">
                      ${job.salary_min.toLocaleString()} - ${job.salary_max.toLocaleString()}
                    </span>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Remote</span>
                  <span className="text-sm">{job.is_remote ? "Yes" : "No"}</span>
                </div>
                {job.match_score != null && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Match Score</span>
                    <Badge variant="info">{job.match_score}%</Badge>
                  </div>
                )}
                {job.url && (
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm text-primary hover:underline"
                  >
                    <ExternalLink className="h-4 w-4" />
                    View Original Listing
                  </a>
                )}
              </CardContent>
            </Card>

            {job.skills_required && job.skills_required.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Required Skills</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {job.skills_required.map((skill) => (
                      <Badge key={skill} variant="secondary">{skill}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle>AI Tools</CardTitle>
                <CardDescription>Enhance your application</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={handleTailorResume}
                  disabled={tailoring || resumes.length === 0}
                >
                  {tailoring ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="mr-2 h-4 w-4" />
                  )}
                  Tailor Resume
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={handleGenerateCoverLetter}
                  disabled={generatingLetter || resumes.length === 0}
                >
                  {generatingLetter ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <FileText className="mr-2 h-4 w-4" />
                  )}
                  Generate Cover Letter
                </Button>
                {resumes.length === 0 && (
                  <p className="text-xs text-muted-foreground">
                    Upload a resume first to use AI tools
                  </p>
                )}
              </CardContent>
            </Card>

            {coverLetter && (
              <Card>
                <CardHeader>
                  <CardTitle>Generated Cover Letter</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="whitespace-pre-wrap text-sm">{coverLetter}</div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}

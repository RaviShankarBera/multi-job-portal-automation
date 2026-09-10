"use client"

import React, { useState, useEffect, useRef } from "react"
import {
  FileText,
  Upload,
  Download,
  Trash2,
  Star,
  CheckCircle,
  Clock,
  AlertCircle,
  Loader2,
} from "lucide-react"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import api from "@/lib/api"
import type { Resume } from "@/types"

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes"
  const k = 1024
  const sizes = ["Bytes", "KB", "MB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
}

function getAtsScoreColor(score: number): string {
  if (score >= 80) return "text-green-600 bg-green-100 dark:bg-green-900/50"
  if (score >= 60) return "text-yellow-600 bg-yellow-100 dark:bg-yellow-900/50"
  return "text-red-600 bg-red-100 dark:bg-red-900/50"
}

export default function ResumesPage() {
  const [resumes, setResumes] = useState<Resume[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    fetchResumes()
  }, [])

  const fetchResumes = async () => {
    try {
      const data = await api.getResumes()
      setResumes(data)
    } catch (err: any) {
      setError(err?.message || "Failed to load resumes")
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setError("")
    try {
      const uploaded = await api.uploadResume(file)
      setResumes([uploaded, ...resumes])
    } catch (err: any) {
      setError(err?.message || "Failed to upload resume")
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ""
    }
  }

  const setPrimary = async (id: number) => {
    try {
      const updated = await api.setPrimaryResume(id)
      setResumes(resumes.map((r) => (r.id === id ? { ...r, is_primary: true } : { ...r, is_primary: false })))
    } catch (err: any) {
      setError(err?.message || "Failed to set primary resume")
    }
  }

  const deleteResume = async (id: number) => {
    try {
      await api.deleteResume(id)
      setResumes(resumes.filter((r) => r.id !== id))
    } catch (err: any) {
      setError(err?.message || "Failed to delete resume")
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Resumes</h1>
            <p className="text-muted-foreground">
              Manage your resumes and track their ATS compatibility
            </p>
          </div>
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.doc,.docx"
              className="hidden"
              onChange={handleUpload}
            />
            <Button onClick={() => fileInputRef.current?.click()} disabled={uploading}>
              {uploading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Upload className="mr-2 h-4 w-4" />
              )}
              {uploading ? "Uploading..." : "Upload Resume"}
            </Button>
          </div>
        </div>

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}

        {!loading && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {resumes.map((resume) => (
              <Card key={resume.id} className={resume.is_primary ? "ring-2 ring-primary" : ""}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <div className="rounded-lg bg-primary/10 p-2">
                        <FileText className="h-5 w-5 text-primary" />
                      </div>
                      {resume.is_primary && (
                        <Badge variant="success" className="text-xs">
                          Active
                        </Badge>
                      )}
                    </div>
                    {resume.ats_score != null && (
                      <div className={`rounded-lg px-2 py-1 text-sm font-medium ${getAtsScoreColor(resume.ats_score)}`}>
                        ATS: {resume.ats_score}
                      </div>
                    )}
                  </div>
                  <CardTitle className="text-lg mt-2">{resume.original_filename}</CardTitle>
                  <CardDescription>{resume.filename}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(resume.created_at).toLocaleDateString()}
                      </span>
                      <span>{formatFileSize(resume.file_size)}</span>
                    </div>

                    {resume.extracted_skills && resume.extracted_skills.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {resume.extracted_skills.slice(0, 5).map((skill) => (
                          <Badge key={skill} variant="secondary" className="text-xs">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    )}

                    <div className="flex gap-2">
                      {!resume.is_primary ? (
                        <Button
                          size="sm"
                          variant="outline"
                          className="flex-1"
                          onClick={() => setPrimary(resume.id)}
                        >
                          <Star className="mr-1 h-3 w-3" />
                          Set Active
                        </Button>
                      ) : (
                        <Button size="sm" variant="outline" className="flex-1" disabled>
                          <CheckCircle className="mr-1 h-3 w-3" />
                          Active
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => deleteResume(resume.id)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Upload className="h-10 w-10 text-muted-foreground mb-4" />
                <p className="text-sm text-muted-foreground mb-2">
                  Upload a new resume
                </p>
                <p className="text-xs text-muted-foreground mb-4">
                  PDF, DOC, or DOCX (max 5MB)
                </p>
                <Button
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                >
                  Choose File
                </Button>
              </CardContent>
            </Card>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle>ATS Score Guide</CardTitle>
            <CardDescription>
              Understanding your resume&apos;s compatibility with Applicant Tracking Systems
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="flex items-start gap-3">
                <div className="rounded-full bg-green-100 p-2 dark:bg-green-900/50">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                </div>
                <div>
                  <h4 className="font-medium">80-100: Excellent</h4>
                  <p className="text-sm text-muted-foreground">
                    Your resume is highly compatible with ATS systems
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="rounded-full bg-yellow-100 p-2 dark:bg-yellow-900/50">
                  <AlertCircle className="h-4 w-4 text-yellow-600" />
                </div>
                <div>
                  <h4 className="font-medium">60-79: Good</h4>
                  <p className="text-sm text-muted-foreground">
                    Some improvements could help bypass ATS filters
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="rounded-full bg-red-100 p-2 dark:bg-red-900/50">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                </div>
                <div>
                  <h4 className="font-medium">Below 60: Needs Work</h4>
                  <p className="text-sm text-muted-foreground">
                    Consider reformatting to improve ATS compatibility
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}

"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import {
  Search,
  Building2,
  MapPin,
  Clock,
  Filter,
  MoreHorizontal,
  ExternalLink,
  Calendar,
  FileText,
  Loader2,
  CheckCircle,
} from "lucide-react"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@radix-ui/react-dropdown-menu"
import api from "@/lib/api"
import type { Application } from "@/types"

type ApplicationStatus = "saved" | "applied" | "screening" | "interview" | "offer" | "rejected"

const statusConfig: Record<ApplicationStatus, { label: string; color: string }> = {
  saved: { label: "Saved", color: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100" },
  applied: { label: "Applied", color: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100" },
  screening: { label: "Screening", color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100" },
  interview: { label: "Interview", color: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100" },
  offer: { label: "Offer", color: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100" },
  rejected: { label: "Rejected", color: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100" },
}

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<ApplicationStatus | "all">("all")
  const [updatingId, setUpdatingId] = useState<number | null>(null)

  useEffect(() => {
    fetchApplications()
  }, [statusFilter])

  const fetchApplications = async () => {
    setLoading(true)
    setError("")
    try {
      const status = statusFilter === "all" ? undefined : statusFilter
      const data = await api.getApplications(status)
      setApplications(data)
    } catch (err: any) {
      setError(err?.message || "Failed to load applications")
    } finally {
      setLoading(false)
    }
  }

  const handleStatusUpdate = async (id: number, newStatus: string) => {
    setUpdatingId(id)
    try {
      const updated = await api.updateApplicationStatus(id, newStatus)
      setApplications(applications.map((app) => (app.id === id ? updated : app)))
    } catch (err: any) {
      setError(err?.message || "Failed to update status")
    } finally {
      setUpdatingId(null)
    }
  }

  const filteredApplications = applications.filter((app) => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return (
      app.job?.title?.toLowerCase().includes(q) ||
      app.job?.company?.toLowerCase().includes(q) ||
      false
    )
  })

  const statusCounts = applications.reduce((acc, app) => {
    acc[app.status] = (acc[app.status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Applications</h1>
          <p className="text-muted-foreground">
            Track and manage your job applications
          </p>
        </div>

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-6">
          {(Object.keys(statusConfig) as ApplicationStatus[]).map((status) => (
            <Card
              key={status}
              className={`cursor-pointer transition-all hover:shadow-md ${
                statusFilter === status ? "ring-2 ring-primary" : ""
              }`}
              onClick={() => setStatusFilter(statusFilter === status ? "all" : status)}
            >
              <CardContent className="p-4">
                <div className="text-center">
                  <div className="text-2xl font-bold">{statusCounts[status] || 0}</div>
                  <div className="text-sm text-muted-foreground">{statusConfig[status].label}</div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="flex flex-col gap-4 md:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search applications..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}

        {!loading && (
          <div className="space-y-4">
            {filteredApplications.map((app) => (
              <Card key={app.id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-semibold">{app.job?.title || `Job #${app.job_id}`}</h3>
                        <Badge className={statusConfig[app.status as ApplicationStatus]?.color || ""}>
                          {statusConfig[app.status as ApplicationStatus]?.label || app.status}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        {app.job?.company && (
                          <span className="flex items-center gap-1">
                            <Building2 className="h-4 w-4" />
                            {app.job.company}
                          </span>
                        )}
                        {app.job?.location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="h-4 w-4" />
                            {app.job.location}
                          </span>
                        )}
                        {app.applied_at && (
                          <span className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            Applied {new Date(app.applied_at).toLocaleDateString()}
                          </span>
                        )}
                        {app.resume && (
                          <span className="flex items-center gap-1">
                            <FileText className="h-4 w-4" />
                            {app.resume.original_filename}
                          </span>
                        )}
                      </div>
                      {app.notes && (
                        <p className="text-sm text-muted-foreground">{app.notes}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {app.job_id && (
                        <Button variant="ghost" size="icon" asChild>
                          <Link href={`/jobs/${app.job_id}`}>
                            <ExternalLink className="h-4 w-4" />
                          </Link>
                        </Button>
                      )}
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            {updatingId === app.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <MoreHorizontal className="h-4 w-4" />
                            )}
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleStatusUpdate(app.id, "applied")}>
                            Mark Applied
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleStatusUpdate(app.id, "screening")}>
                            Mark Screening
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleStatusUpdate(app.id, "interview")}>
                            Mark Interview
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleStatusUpdate(app.id, "offer")}>
                            Mark Offer
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleStatusUpdate(app.id, "rejected")}>
                            Mark Rejected
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {!loading && filteredApplications.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Search className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium">No applications found</h3>
              <p className="text-sm text-muted-foreground">
                {applications.length === 0
                  ? "Start applying to jobs to see them here"
                  : "Try adjusting your search or filters"}
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}

"use client"

import React, { useState } from "react"
import {
  Save,
  Bell,
  Globe,
  Moon,
  Sun,
  Shield,
  Trash2,
  AlertTriangle,
  Loader2,
} from "lucide-react"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { useTheme } from "@/hooks/use-theme"

export default function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const [emailNotifications, setEmailNotifications] = useState(true)
  const [jobAlerts, setJobAlerts] = useState(true)
  const [weeklyDigest, setWeeklyDigest] = useState(false)
  const [autoApply, setAutoApply] = useState(false)
  const [matchThreshold, setMatchThreshold] = useState(70)
  const [automationMode, setAutomationMode] = useState("review")
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState("")

  const handleSave = async () => {
    setSaving(true)
    setSuccess("")
    await new Promise((resolve) => setTimeout(resolve, 1000))
    setSaving(false)
    setSuccess("Settings saved successfully")
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
            <p className="text-muted-foreground">
              Manage your account preferences and configurations
            </p>
          </div>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-2 h-4 w-4" />
            )}
            {saving ? "Saving..." : "Save Changes"}
          </Button>
        </div>

        {success && (
          <div className="rounded-md bg-green-100 p-3 text-sm text-green-800 dark:bg-green-900/50 dark:text-green-200">
            {success}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5" />
                  Notifications
                </CardTitle>
                <CardDescription>
                  Configure how you receive notifications
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Email Notifications</Label>
                    <p className="text-sm text-muted-foreground">
                      Receive email updates about your applications
                    </p>
                  </div>
                  <Button
                    variant={emailNotifications ? "default" : "outline"}
                    size="sm"
                    onClick={() => setEmailNotifications(!emailNotifications)}
                  >
                    {emailNotifications ? "Enabled" : "Disabled"}
                  </Button>
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Job Alerts</Label>
                    <p className="text-sm text-muted-foreground">
                      Get notified about new job matches
                    </p>
                  </div>
                  <Button
                    variant={jobAlerts ? "default" : "outline"}
                    size="sm"
                    onClick={() => setJobAlerts(!jobAlerts)}
                  >
                    {jobAlerts ? "Enabled" : "Disabled"}
                  </Button>
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Weekly Digest</Label>
                    <p className="text-sm text-muted-foreground">
                      Receive a weekly summary of your job search
                    </p>
                  </div>
                  <Button
                    variant={weeklyDigest ? "default" : "outline"}
                    size="sm"
                    onClick={() => setWeeklyDigest(!weeklyDigest)}
                  >
                    {weeklyDigest ? "Enabled" : "Disabled"}
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="h-5 w-5" />
                  Preferences
                </CardTitle>
                <CardDescription>
                  Customize your experience
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Appearance</Label>
                    <p className="text-sm text-muted-foreground">
                      Toggle between light and dark mode
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant={theme === "light" ? "default" : "outline"}
                      size="sm"
                      onClick={() => setTheme("light")}
                    >
                      <Sun className="mr-2 h-4 w-4" />
                      Light
                    </Button>
                    <Button
                      variant={theme === "dark" ? "default" : "outline"}
                      size="sm"
                      onClick={() => setTheme("dark")}
                    >
                      <Moon className="mr-2 h-4 w-4" />
                      Dark
                    </Button>
                    <Button
                      variant={theme === "system" ? "default" : "outline"}
                      size="sm"
                      onClick={() => setTheme("system")}
                    >
                      System
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Account
                </CardTitle>
                <CardDescription>
                  Manage your account settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label>Email Address</Label>
                  <Input type="email" placeholder="your@email.com" disabled />
                </div>
                <div className="space-y-2">
                  <Label>Change Password</Label>
                  <Input type="password" placeholder="Enter new password" />
                </div>
                <div className="pt-4 border-t">
                  <h4 className="text-sm font-medium text-destructive mb-2">
                    Danger Zone
                  </h4>
                  <p className="text-sm text-muted-foreground mb-4">
                    Once you delete your account, there is no going back.
                  </p>
                  <Button variant="destructive">
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete Account
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Automation Settings</CardTitle>
                <CardDescription>
                  Configure your job search automation
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label>Automation Mode</Label>
                  <select
                    value={automationMode}
                    onChange={(e) => setAutomationMode(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="auto">Auto - Apply automatically</option>
                    <option value="review">Review - Approve before applying</option>
                    <option value="manual">Manual - No automation</option>
                  </select>
                  <p className="text-xs text-muted-foreground">
                    Control how the system handles job applications
                  </p>
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Auto-Apply</Label>
                    <p className="text-sm text-muted-foreground">
                      Automatically apply to matching jobs
                    </p>
                  </div>
                  <Button
                    variant={autoApply ? "default" : "outline"}
                    size="sm"
                    onClick={() => setAutoApply(!autoApply)}
                  >
                    {autoApply ? "Enabled" : "Disabled"}
                  </Button>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Match Threshold</Label>
                    <Badge variant="secondary">{matchThreshold}%</Badge>
                  </div>
                  <input
                    type="range"
                    min="50"
                    max="100"
                    value={matchThreshold}
                    onChange={(e) => setMatchThreshold(parseInt(e.target.value))}
                    className="w-full"
                  />
                  <p className="text-xs text-muted-foreground">
                    Only auto-apply to jobs with this match score or higher
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-amber-500" />
                  Important Notes
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <p>
                  Auto-apply feature will use your active resume and default cover letter.
                </p>
                <p>
                  You can review and cancel auto-applications in the Applications tab.
                </p>
                <p>
                  Match threshold affects both auto-apply and job recommendations.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}

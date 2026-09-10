import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(date))
}

export function formatRelativeTime(date: string | Date): string {
  const now = new Date()
  const target = new Date(date)
  const diff = now.getTime() - target.getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  const weeks = Math.floor(days / 7)
  const months = Math.floor(days / 30)

  if (months > 0) return `${months} month${months > 1 ? "s" : ""} ago`
  if (weeks > 0) return `${weeks} week${weeks > 1 ? "s" : ""} ago`
  if (days > 0) return `${days} day${days > 1 ? "s" : ""} ago`
  if (hours > 0) return `${hours} hour${hours > 1 ? "s" : ""} ago`
  if (minutes > 0) return `${minutes} minute${minutes > 1 ? "s" : ""} ago`
  return "just now"
}

export function formatCurrency(amount: number, currency: string = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes"
  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    saved: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100",
    applied: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100",
    screening: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100",
    interview: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100",
    offer: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
    rejected: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
    accepted: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-100",
  }
  return colors[status] || colors.saved
}

export function getJobTypeColor(type: string): string {
  const colors: Record<string, string> = {
    "full-time": "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100",
    "part-time": "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-100",
    contract: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100",
    remote: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
  }
  return colors[type] || colors["full-time"]
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + "..."
}

export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout
  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 9)
}

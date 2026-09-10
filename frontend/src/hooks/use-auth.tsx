"use client"

import { useState, useEffect, useCallback, createContext, useContext } from "react"
import type { User } from "@/types"
import api from "@/lib/api"

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchUser = useCallback(async () => {
    const token = api.getToken()
    if (!token) {
      setLoading(false)
      return
    }

    try {
      const userData = await api.getMe()
      setUser(userData)
    } catch {
      api.setToken(null)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  const login = async (email: string, password: string) => {
    const response = await api.login(email, password)
    api.setToken(response.access_token)
    const userData = await api.getMe()
    setUser(userData)
  }

  const register = async (email: string, password: string, fullName?: string) => {
    const response = await api.register(email, password, fullName)
    api.setToken(response.access_token)
    const userData = await api.getMe()
    setUser(userData)
  }

  const logout = () => {
    api.setToken(null)
    setUser(null)
    window.location.href = "/login"
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}

export default useAuth

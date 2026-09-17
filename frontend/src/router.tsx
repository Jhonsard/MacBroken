import { createBrowserRouter, Navigate } from "react-router-dom"

import { AppLayout } from "@/components/layouts/AppLayout"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { DashboardPage } from "@/pages/DashboardPage"
import { HomePage } from "@/pages/HomePage"
import { LoginPage } from "@/pages/LoginPage"
import { SignUpPage } from "@/pages/SignUpPage"

export const router = createBrowserRouter([
  { path: "/", element: <HomePage /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/signup", element: <SignUpPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [{ path: "/dashboard", element: <DashboardPage /> }],
      },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
])
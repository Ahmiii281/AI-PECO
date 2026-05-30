import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import authService from '../services/auth';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [isValidated, setIsValidated] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Validate token on mount
    const validateAuth = async () => {
      if (!authService.isAuthenticated()) {
        setIsValidated(true);
        return;
      }

      try {
        // Try to fetch profile to validate token
        await authService.getProfile();
        setIsAuthenticated(true);
      } catch (err) {
        // Token is invalid or expired
        authService.logout();
        setIsAuthenticated(false);
      }
      setIsValidated(true);
    };

    validateAuth();
  }, []);

  if (!isValidated) {
    return (
      <div className="flex items-center justify-center h-full w-full bg-gray-50 dark:bg-gray-800">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

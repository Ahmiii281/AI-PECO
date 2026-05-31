import React, { useEffect, useState } from 'react';
import { useNavigate, Link, useLocation, useSearchParams } from 'react-router-dom';
import authService from '../services/auth';
import './Auth.css';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [view, setView] = useState<'login' | 'forgot' | 'reset'>('login');
  const [successMessage, setSuccessMessage] = useState('');
  const [searchParams] = useSearchParams();
  const location = useLocation();

  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      setResetToken(token);
      setView('reset');
      setError('');
      setSuccessMessage('');
      return;
    }

    if (location.pathname === '/reset-password') {
      setView('reset');
      setError('');
      setSuccessMessage('');
    }
  }, [searchParams, location.pathname]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authService.login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    setLoading(true);
    try {
      await authService.forgotPassword(email);
      setSuccessMessage('Check your email for the reset token. Paste it below to reset your password.');
      setView('reset');
    } catch (err: any) {
      setError(err.message || 'Failed to send reset link');
    } finally {
      setLoading(false);
    }
  };

  const handleResetSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      await authService.resetPassword(resetToken, newPassword);
      setSuccessMessage('Password reset successfully! Redirecting to login...');
      setTimeout(() => {
        setView('login');
        setResetToken('');
        setNewPassword('');
        setConfirmPassword('');
        setEmail('');
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Password reset failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>AI-PECO</h1>
        <h2>Login</h2>

        {error && <div className="error-message">{error}</div>}

        {view === 'login' && (
          <>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  required
                />
              </div>

              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
                <div style={{ textAlign: 'right', marginTop: '0.5rem' }}>
                  <button
                    type="button"
                    className="forgot-link"
                    onClick={() => { setView('forgot'); setError(''); setSuccessMessage(''); }}
                  >
                    Forgot password?
                  </button>
                </div>
              </div>

              <button type="submit" disabled={loading}>
                {loading ? 'Logging in...' : 'Login'}
              </button>
            </form>

            <p className="auth-link">
              Don't have an account? <Link to="/register">Register here</Link>
            </p>
          </>
        )}

        {view === 'forgot' && (
          <>
            <button
              type="button"
              className="back-link"
              onClick={() => { setView('login'); setError(''); setSuccessMessage(''); }}
            >
              ← Back to Login
            </button>

            <h2 style={{ marginTop: '0.5rem' }}>Request Password Reset</h2>
            <p style={{ color: '#b0b0b0' }}>Enter your email and we'll send you a reset token.</p>

            {successMessage && <div className="success-message">{successMessage}</div>}

            <form onSubmit={handleForgotSubmit}>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  required
                />
              </div>

              <button type="submit" disabled={loading}>
                {loading ? 'Sending...' : 'Send Reset Token'}
              </button>
            </form>
          </>
        )}

        {view === 'reset' && (
          <>
            <button
              type="button"
              className="back-link"
              onClick={() => { setView('login'); setError(''); setSuccessMessage(''); }}
            >
              ← Back to Login
            </button>

            <h2 style={{ marginTop: '0.5rem' }}>Reset Password</h2>
            <p style={{ color: '#b0b0b0' }}>Paste the token from your email and enter a new password.</p>

            {successMessage && <div className="success-message">{successMessage}</div>}

            <form onSubmit={handleResetSubmit}>
              <div className="form-group">
                <label>Reset Token</label>
                <input
                  type="text"
                  value={resetToken}
                  onChange={(e) => setResetToken(e.target.value)}
                  placeholder="Paste your reset token here"
                  required
                />
              </div>

              <div className="form-group">
                <label>New Password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
              </div>

              <div className="form-group">
                <label>Confirm Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
              </div>

              <button type="submit" disabled={loading}>
                {loading ? 'Resetting...' : 'Reset Password'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

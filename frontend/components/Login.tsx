import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import authService from '../services/auth';
import './Auth.css';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [view, setView] = useState<'login' | 'forgot'>('login');
  const [successMessage, setSuccessMessage] = useState('');

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
      setSuccessMessage('Check your inbox for a reset link.');
    } catch (err: any) {
      setError(err.message || 'Failed to send reset link');
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
                  <span className="forgot-link" onClick={() => { setView('forgot'); setError(''); setSuccessMessage(''); }}>
                    Forgot password?
                  </span>
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
            <a className="back-link" onClick={() => { setView('login'); setError(''); setSuccessMessage(''); }}>
              ← Back to Login
            </a>

            <h2 style={{ marginTop: '0.5rem' }}>Reset Password</h2>
            <p style={{ color: '#b0b0b0' }}>Enter your email and we'll send you a reset link.</p>

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
                {loading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

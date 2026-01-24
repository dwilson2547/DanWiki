import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BookOpen } from 'lucide-react';

export default function Register() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    display_name: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingApproval, setPendingApproval] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);

    try {
      const result = await register({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        display_name: formData.display_name || formData.username
      });
      
      if (result.pending_approval) {
        setPendingApproval(true);
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card card">
        <div className="card-body">
          <div className="flex justify-center mb-4">
            <BookOpen size={48} style={{ color: 'var(--primary)' }} />
          </div>
          
          {pendingApproval ? (
            <>
              <h1 className="auth-title">Registration Successful!</h1>
              <div className="alert alert-info" style={{ marginTop: '1.5rem', marginBottom: '1.5rem' }}>
                <p style={{ marginBottom: '0.5rem' }}>
                  <strong>Your account has been created and is pending administrator approval.</strong>
                </p>
                <p style={{ fontSize: '0.875rem', margin: 0 }}>
                  You'll be able to log in once an administrator approves your account. 
                  This usually happens within 24 hours.
                </p>
              </div>
              <Link to="/login" className="btn btn-primary w-full" style={{ marginTop: '1rem' }}>
                Go to Login
              </Link>
              <p className="text-center mt-4 text-sm text-secondary">
                <Link to="/">← Back to Home</Link>
              </p>
            </>
          ) : (
            <>
              <h1 className="auth-title">Create an account</h1>
              <p className="auth-subtitle">Get started with your wiki</p>

              {error && (
                <div className="alert alert-error">{error}</div>
              )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Username</label>
              <input
                type="text"
                name="username"
                className="form-input"
                value={formData.username}
                onChange={handleChange}
                required
                minLength={3}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Email</label>
              <input
                type="email"
                name="email"
                className="form-input"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Display Name (optional)</label>
              <input
                type="text"
                name="display_name"
                className="form-input"
                value={formData.display_name}
                onChange={handleChange}
                placeholder="How others will see you"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                name="password"
                className="form-input"
                value={formData.password}
                onChange={handleChange}
                required
                minLength={8}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Confirm Password</label>
              <input
                type="password"
                name="confirmPassword"
                className="form-input"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary w-full"
              disabled={loading}
            >
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </form>

          <p className="text-center mt-4 text-sm text-secondary">
            Already have an account?{' '}
            <Link to="/login">Sign in</Link>
          </p>
          <p className="text-center mt-2 text-sm text-secondary">
            <Link to="/">← Back to Home</Link>
          </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

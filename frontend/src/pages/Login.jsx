import { Link, useLocation } from 'react-router-dom';
import { BookOpen, LogIn } from 'lucide-react';

// Sign-in is through authentik only; the backend starts the OIDC flow.
export default function Login() {
  const error = useLocation().state?.error;

  return (
    <div className="auth-container">
      <div className="auth-card card">
        <div className="card-body">
          <div className="flex justify-center mb-4">
            <BookOpen size={48} className="text-primary" style={{ color: 'var(--primary)' }} />
          </div>
          <h1 className="auth-title">Welcome</h1>
          <p className="auth-subtitle">Sign in with your danwils account</p>

          {error && (
            <div className="alert alert-error">{error}</div>
          )}

          <a href="/api/auth/oidc/login" className="btn btn-primary w-full">
            <LogIn size={18} />
            Sign in
          </a>

          <p className="text-center mt-4 text-sm text-secondary">
            New here? Choose "Sign in with Google" on the next page; new accounts wait for approval.
          </p>
          <p className="text-center mt-2 text-sm text-secondary">
            <Link to="/">← Back to Home</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

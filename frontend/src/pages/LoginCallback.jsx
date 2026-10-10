import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// The backend's authentik callback lands here with tokens (or an error) in the URL
// fragment, which is never sent to a server.
export default function LoginCallback() {
  const { completeLogin } = useAuth();
  const navigate = useNavigate();
  const handled = useRef(false);

  useEffect(() => {
    if (handled.current) return;
    handled.current = true;
    const params = new URLSearchParams(window.location.hash.slice(1));
    window.history.replaceState(null, '', window.location.pathname);
    const access = params.get('access_token');
    const refresh = params.get('refresh_token');
    if (!access || !refresh) {
      navigate('/login', { replace: true, state: { error: params.get('error') || 'Sign-in failed' } });
      return;
    }
    completeLogin(access, refresh)
      .then(() => navigate('/dashboard', { replace: true }))
      .catch(() => navigate('/login', { replace: true, state: { error: 'Sign-in failed' } }));
  }, [completeLogin, navigate]);

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
      <div className="spinner" />
    </div>
  );
}

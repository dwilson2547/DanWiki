import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    console.log('AuthContext: Checking token on mount', token ? 'Token exists' : 'No token');
    if (token) {
      authAPI.getMe()
        .then(response => {
          console.log('AuthContext: getMe success', response.data.user);
          setUser(response.data.user);
        })
        .catch((error) => {
          console.log('AuthContext: getMe failed', error.response?.status, error.message);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  // Tokens come from the authentik sign-in callback (pages/LoginCallback.jsx).
  const completeLogin = async (accessToken, refreshToken) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    const response = await authAPI.getMe();
    setUser(response.data.user);
    return response.data.user;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  // Also end the authentik session, so the next sign-in asks again.
  const signOut = () => {
    logout();
    window.location.href = '/api/auth/oidc/logout';
  };

  const refreshUser = async () => {
    try {
      const response = await authAPI.getMe();
      setUser(response.data.user);
      return response.data.user;
    } catch (error) {
      console.error('Failed to refresh user:', error);
      throw error;
    }
  };

  const updateUser = (userData) => {
    setUser(prev => ({ ...prev, ...userData }));
  };

  return (
    <AuthContext.Provider value={{ user, loading, completeLogin, logout, signOut, refreshUser, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      if (token) {
        try {
          const userData = await authService.getMe();
          setUser(userData);
        } catch (err) {
          console.error("Failed to restore session", err);
          logout();
        }
      }
      setLoading(false);
    };

    fetchUser();
  }, [token]);

  const login = async (email, password) => {
    const res = await authService.login(email, password);
    localStorage.setItem('token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    return res.user;
  };

  const register = async (name, email, password) => {
    const res = await authService.register(name, email, password);
    localStorage.setItem('token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    return res.user;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const connectGmail = async () => {
    try {
      const res = await authService.getGoogleAuthUrl();
      if (res.url && !res.url.includes("mock=true")) {
        window.location.href = res.url;
      } else {
        // Direct connect in dev/demo mode
        await authService.connectGmailDirect(user?.email);
        const updatedUser = await authService.getMe();
        setUser(updatedUser);
      }
    } catch (err) {
      console.error("Connect Gmail failed, using direct connection fallback", err);
      await authService.connectGmailDirect(user?.email);
      const updatedUser = await authService.getMe();
      setUser(updatedUser);
    }
  };

  const handleGoogleCallback = async (code) => {
    const res = await authService.googleCallback(code);
    const updatedUser = await authService.getMe();
    setUser(updatedUser);
    return res;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        connectGmail,
        handleGoogleCallback,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { CheckCircle2, AlertCircle } from 'lucide-react';

const AuthCallback = () => {
  const [searchParams] = useSearchParams();
  const { handleGoogleCallback } = useAuth();
  const navigate = useNavigate();
  const [status, setStatus] = useState('Connecting Gmail account...');
  const [error, setError] = useState('');

  useEffect(() => {
    const code = searchParams.get('code');
    if (code) {
      handleGoogleCallback(code)
        .then(() => {
          setStatus('Gmail account connected successfully! Redirecting...');
          setTimeout(() => navigate('/dashboard'), 1500);
        })
        .catch((err) => {
          console.error(err);
          setError('Failed to complete Gmail authorization.');
        });
    } else {
      setError('No authorization code found in callback URL.');
    }
  }, [searchParams]);

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-8 max-w-md w-full text-center space-y-4 shadow-2xl border border-slate-800">
        {error ? (
          <>
            <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
            <h2 className="text-lg font-bold text-slate-900">Connection Failed</h2>
            <p className="text-xs text-slate-500">{error}</p>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-4 py-2 bg-slate-900 text-white rounded-xl text-xs font-semibold"
            >
              Return to Dashboard
            </button>
          </>
        ) : (
          <>
            <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto animate-bounce" />
            <h2 className="text-lg font-bold text-slate-900">Gmail Integration</h2>
            <p className="text-xs text-slate-600 font-medium">{status}</p>
          </>
        )}
      </div>
    </div>
  );
};

export default AuthCallback;

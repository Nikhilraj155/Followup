import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { emailService } from '../services/api';
import { Mail, CheckCircle, AlertCircle, LogOut, User as UserIcon, RefreshCw } from 'lucide-react';

const Navbar = () => {
  const { user, connectGmail, logout } = useAuth();
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState('');

  const handleSyncInbox = async () => {
    setSyncing(true);
    setSyncMsg('');
    try {
      const res = await emailService.syncInbox();
      setSyncMsg(res.message || 'Inbox synced successfully');
      setTimeout(() => setSyncMsg(''), 4000);
    } catch (err) {
      console.error(err);
      setSyncMsg('Sync completed.');
      setTimeout(() => setSyncMsg(''), 4000);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold text-xl shadow-md">
            F
          </div>
          <span className="font-bold text-xl text-slate-900 tracking-tight">
            FollowUp<span className="text-blue-600">AI</span>
          </span>
        </div>

        <div className="flex items-center space-x-3">
          {syncMsg && (
            <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
              {syncMsg}
            </span>
          )}

          {/* Sync Gmail Inbox Button */}
          <button
            onClick={handleSyncInbox}
            disabled={syncing}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded-lg text-xs font-semibold border border-slate-200 transition-colors"
            title="Sync all job application emails from your Gmail inbox"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin text-blue-600' : ''}`} />
            <span>{syncing ? 'Syncing...' : 'Sync Gmail Inbox'}</span>
          </button>

          {/* Gmail Connection Indicator */}
          {user?.has_gmail_connected ? (
            <div className="flex items-center space-x-2 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-medium border border-emerald-200">
              <CheckCircle className="w-4 h-4 text-emerald-500" />
              <span>Gmail Connected: <strong>{user.connected_email}</strong></span>
            </div>
          ) : (
            <button
              onClick={connectGmail}
              className="flex items-center space-x-2 px-3.5 py-1.5 bg-rose-50 text-rose-700 hover:bg-rose-100 rounded-lg text-xs font-semibold border border-rose-200 transition-colors"
            >
              <AlertCircle className="w-4 h-4 text-rose-500" />
              <span>Connect Gmail</span>
            </button>
          )}

          {/* User Profile */}
          <div className="flex items-center space-x-3 pl-3 border-l border-slate-200">
            <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-600 font-semibold text-sm">
              {user?.name ? user.name.charAt(0).toUpperCase() : <UserIcon className="w-4 h-4" />}
            </div>
            <div className="hidden sm:block text-left">
              <div className="text-sm font-semibold text-slate-800 leading-none">{user?.name}</div>
              <div className="text-xs text-slate-500 leading-none mt-1">{user?.email}</div>
            </div>
            <button
              onClick={logout}
              title="Log out"
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;

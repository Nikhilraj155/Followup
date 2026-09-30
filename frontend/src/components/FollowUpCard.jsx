import React, { useState } from 'react';
import { Sparkles, Edit2, Send, RefreshCw, XCircle, CheckCircle } from 'lucide-react';
import StatusBadge from './StatusBadge';

const FollowUpCard = ({ followup, onApprove, onRegenerate, onCancel, onUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [subject, setSubject] = useState(followup.subject || '');
  const [body, setBody] = useState(followup.body || '');
  const [loadingAction, setLoadingAction] = useState(null);

  const handleSave = async () => {
    setLoadingAction('save');
    try {
      await onUpdate(followup.id, { subject, body });
      setIsEditing(false);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleApprove = async () => {
    setLoadingAction('approve');
    try {
      await onApprove(followup.id);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleRegenerate = async () => {
    setLoadingAction('regenerate');
    try {
      await onRegenerate(followup.id);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleCancel = async () => {
    setLoadingAction('cancel');
    try {
      await onCancel(followup.id);
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden mb-6 transition-all hover:shadow-md">
      <div className="bg-slate-950 text-white p-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-5 h-5 text-amber-400" />
          <span className="font-semibold text-sm">AI Generated Follow-up #{followup.follow_up_number}</span>
        </div>
        <StatusBadge status={followup.status} />
      </div>

      <div className="p-6 space-y-4">
        {isEditing ? (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Subject</label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Email Body</label>
              <textarea
                rows={8}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
            <div className="flex space-x-2">
              <button
                onClick={handleSave}
                disabled={loadingAction === 'save'}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700"
              >
                {loadingAction === 'save' ? 'Saving...' : 'Save Changes'}
              </button>
              <button
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 bg-slate-100 text-slate-600 rounded-lg text-xs font-semibold hover:bg-slate-200"
              >
                Cancel Edit
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Subject</div>
            <div className="text-base font-semibold text-slate-900 mb-4">{followup.subject || 'No subject'}</div>
            
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Body Preview</div>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm text-slate-800 whitespace-pre-wrap font-sans leading-relaxed">
              {followup.body || 'No draft generated yet.'}
            </div>
          </div>
        )}
      </div>

      <div className="bg-slate-50 px-6 py-4 border-t border-slate-200 flex items-center justify-between flex-wrap gap-3">
        <div className="text-xs text-slate-500">
          Scheduled for: <strong>{new Date(followup.scheduled_at).toLocaleString()}</strong>
        </div>

        <div className="flex items-center space-x-2">
          {!isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center space-x-1 px-3 py-2 bg-white text-slate-700 border border-slate-300 rounded-xl text-xs font-semibold hover:bg-slate-50 transition-colors"
            >
              <Edit2 className="w-3.5 h-3.5" />
              <span>Edit</span>
            </button>
          )}

          <button
            onClick={handleRegenerate}
            disabled={loadingAction === 'regenerate'}
            className="flex items-center space-x-1 px-3 py-2 bg-purple-50 text-purple-700 border border-purple-200 rounded-xl text-xs font-semibold hover:bg-purple-100 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingAction === 'regenerate' ? 'animate-spin' : ''}`} />
            <span>Regenerate</span>
          </button>

          <button
            onClick={handleApprove}
            disabled={loadingAction === 'approve'}
            className="flex items-center space-x-1 px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-semibold hover:bg-blue-700 transition-colors shadow-xs"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{loadingAction === 'approve' ? 'Sending...' : 'Approve & Send'}</span>
          </button>

          <button
            onClick={handleCancel}
            disabled={loadingAction === 'cancel'}
            className="flex items-center space-x-1 px-3 py-2 bg-rose-50 text-rose-700 border border-rose-200 rounded-xl text-xs font-semibold hover:bg-rose-100 transition-colors"
          >
            <XCircle className="w-3.5 h-3.5" />
            <span>Cancel</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default FollowUpCard;

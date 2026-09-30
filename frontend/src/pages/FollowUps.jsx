import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import FollowUpCard from '../components/FollowUpCard';
import StatusBadge from '../components/StatusBadge';
import { followupService } from '../services/api';
import { Sparkles, Mail, CheckCircle2 } from 'lucide-react';

const FollowUps = () => {
  const [followups, setFollowups] = useState([]);
  const [statusFilter, setStatusFilter] = useState('draft');
  const [loading, setLoading] = useState(true);

  const fetchFollowups = async () => {
    setLoading(true);
    try {
      const data = await followupService.getFollowups(statusFilter);
      setFollowups(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFollowups();
  }, [statusFilter]);

  const handleApprove = async (id) => {
    await followupService.approveFollowup(id);
    fetchFollowups();
  };

  const handleRegenerate = async (id) => {
    await followupService.generateFollowup(id);
    fetchFollowups();
  };

  const handleCancel = async (id) => {
    await followupService.cancelFollowup(id);
    fetchFollowups();
  };

  const handleUpdate = async (id, data) => {
    await followupService.updateFollowup(id, data);
    fetchFollowups();
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Follow-ups Management</h1>
          <p className="text-sm text-slate-500 mt-1">Review AI generated follow-up emails before sending</p>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center space-x-2 bg-white p-2 rounded-2xl border border-slate-200 shadow-xs">
          {[
            { id: 'draft', label: 'Drafts Awaiting Approval' },
            { id: 'scheduled', label: 'Scheduled' },
            { id: 'sent', label: 'Sent History' },
            { id: 'cancelled', label: 'Cancelled / Skipped' },
            { id: '', label: 'All Follow-ups' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                statusFilter === tab.id
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Follow-up List */}
        <div>
          {loading ? (
            <div className="py-12 text-center text-slate-500">Loading follow-ups...</div>
          ) : followups.length === 0 ? (
            <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3">
              <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto" />
              <h3 className="text-base font-bold text-slate-900">No follow-ups found in this category</h3>
              <p className="text-sm text-slate-500">
                {statusFilter === 'draft'
                  ? 'All generated follow-up drafts have been reviewed or sent!'
                  : 'No follow-up records match the selected filter.'}
              </p>
            </div>
          ) : (
            followups.map((fu) => (
              <FollowUpCard
                key={fu.id}
                followup={fu}
                onApprove={handleApprove}
                onRegenerate={handleRegenerate}
                onCancel={handleCancel}
                onUpdate={handleUpdate}
              />
            ))
          )}
        </div>
      </div>
    </Layout>
  );
};

export default FollowUps;

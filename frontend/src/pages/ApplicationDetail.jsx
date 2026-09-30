import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Layout from '../components/Layout';
import StatusBadge from '../components/StatusBadge';
import FollowUpCard from '../components/FollowUpCard';
import { applicationService, followupService } from '../services/api';
import { ArrowLeft, Building, Mail, User, Calendar, CheckCircle2, Clock, Sparkles } from 'lucide-react';

const ApplicationDetail = () => {
  const { id } = useParams();
  const [app, setApp] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchAppDetail = async () => {
    setLoading(true);
    try {
      const data = await applicationService.getApplication(id);
      setApp(data);
    } catch (err) {
      console.error(err);
      setError('Failed to load application details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAppDetail();
  }, [id]);

  const handleStatusChange = async (newStatus) => {
    try {
      await applicationService.updateApplication(id, { status: newStatus });
      fetchAppDetail();
    } catch (err) {
      alert('Failed to update status.');
    }
  };

  const handleApproveFollowUp = async (fuId) => {
    await followupService.approveFollowup(fuId);
    fetchAppDetail();
  };

  const handleRegenerateFollowUp = async (fuId) => {
    await followupService.generateFollowup(fuId);
    fetchAppDetail();
  };

  const handleCancelFollowUp = async (fuId) => {
    await followupService.cancelFollowup(fuId);
    fetchAppDetail();
  };

  const handleUpdateFollowUp = async (fuId, data) => {
    await followupService.updateFollowup(fuId, data);
    fetchAppDetail();
  };

  if (loading) {
    return (
      <Layout>
        <div className="py-12 text-center text-slate-500">Loading application details...</div>
      </Layout>
    );
  }

  if (error || !app) {
    return (
      <Layout>
        <div className="py-12 text-center text-rose-600 font-semibold">{error || 'Application not found'}</div>
      </Layout>
    );
  }

  const threadEmails = app.email_thread?.emails || [];
  const activeFollowUp = app.follow_ups?.find(f => f.status === 'draft' || f.status === 'scheduled');

  return (
    <Layout>
      <div className="space-y-6">
        {/* Back Link */}
        <Link to="/applications" className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-500 hover:text-slate-800">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Applications</span>
        </Link>

        {/* Application Header Card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-black text-slate-900">{app.company}</h1>
              <StatusBadge status={app.status} />
            </div>
            <p className="text-base font-medium text-slate-600 flex items-center space-x-2">
              <Building className="w-4 h-4 text-slate-400" />
              <span>{app.job_title}</span>
            </p>
            <div className="flex items-center space-x-4 text-xs text-slate-500 pt-1">
              <span className="flex items-center space-x-1">
                <User className="w-3.5 h-3.5 text-slate-400" />
                <span>HR: <strong>{app.contact?.name || 'HR Team'}</strong> ({app.contact?.email})</span>
              </span>
              <span className="flex items-center space-x-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>Applied: {new Date(app.created_at).toLocaleDateString()}</span>
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <label className="text-xs font-semibold text-slate-500">Status:</label>
            <select
              value={app.status}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="px-3 py-1.5 border border-slate-300 rounded-xl text-xs font-semibold text-slate-800 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              <option value="waiting">Waiting for Response</option>
              <option value="follow_up_scheduled">Follow-up Scheduled</option>
              <option value="replied">HR Replied (Stop Automation)</option>
              <option value="closed">Closed / Offer Declined</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        {/* Pending AI Draft Review Card */}
        {activeFollowUp && (
          <div>
            <h2 className="text-base font-bold text-slate-900 mb-3 flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              <span>Next Scheduled Action</span>
            </h2>
            <FollowUpCard
              followup={activeFollowUp}
              onApprove={handleApproveFollowUp}
              onRegenerate={handleRegenerateFollowUp}
              onCancel={handleCancelFollowUp}
              onUpdate={handleUpdateFollowUp}
            />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Email Thread */}
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
              <Mail className="w-4 h-4 text-blue-600" />
              <span>Email Conversation Thread ({threadEmails.length} messages)</span>
            </h2>

            <div className="space-y-4">
              {threadEmails.map((msg, index) => (
                <div
                  key={msg.id || index}
                  className={`rounded-2xl p-5 border ${
                    msg.email_type === 'reply'
                      ? 'bg-emerald-50/60 border-emerald-200'
                      : msg.email_type === 'follow_up'
                      ? 'bg-blue-50/50 border-blue-200'
                      : 'bg-white border-slate-200'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-xs font-semibold text-slate-700">
                      From: <strong className="text-slate-900">{msg.sender}</strong> → To: <strong>{msg.receiver}</strong>
                    </div>
                    <span className="text-xs text-slate-400 font-medium">
                      {new Date(msg.sent_at || msg.created_at).toLocaleString()}
                    </span>
                  </div>

                  <div className="text-sm font-bold text-slate-900 mb-2">{msg.subject}</div>

                  <div className="text-sm text-slate-700 whitespace-pre-wrap font-sans leading-relaxed bg-white/80 p-3.5 rounded-xl border border-slate-100">
                    {msg.body}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Follow-up Timeline */}
          <div className="space-y-4">
            <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
              <Clock className="w-4 h-4 text-purple-600" />
              <span>Automation Timeline</span>
            </h2>

            <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
              <div className="relative border-l-2 border-slate-200 ml-3 pl-4 space-y-6">
                {/* Initial Application */}
                <div className="relative">
                  <div className="absolute -left-[23px] top-1 w-3 h-3 rounded-full bg-blue-600 ring-4 ring-white" />
                  <div className="text-xs font-bold text-slate-900">Application Sent</div>
                  <div className="text-xs text-slate-500">{new Date(app.created_at).toLocaleString()}</div>
                </div>

                {/* Follow-up history */}
                {app.follow_ups?.map((fu) => (
                  <div key={fu.id} className="relative">
                    <div className={`absolute -left-[23px] top-1 w-3 h-3 rounded-full ring-4 ring-white ${
                      fu.status === 'sent' ? 'bg-emerald-500' : fu.status === 'cancelled' ? 'bg-slate-300' : 'bg-amber-500'
                    }`} />
                    <div className="text-xs font-bold text-slate-900">Follow-up #{fu.follow_up_number}</div>
                    <div className="text-xs text-slate-500">Status: <StatusBadge status={fu.status} /></div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      {fu.sent_at ? `Sent ${new Date(fu.sent_at).toLocaleString()}` : `Scheduled ${new Date(fu.scheduled_at).toLocaleString()}`}
                    </div>
                  </div>
                ))}

                {app.status === 'replied' && (
                  <div className="relative">
                    <div className="absolute -left-[23px] top-1 w-3 h-3 rounded-full bg-emerald-600 ring-4 ring-white" />
                    <div className="text-xs font-bold text-emerald-700 flex items-center space-x-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>HR Replied! Automation Stopped</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default ApplicationDetail;

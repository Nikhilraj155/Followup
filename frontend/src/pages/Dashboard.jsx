import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import StatusBadge from '../components/StatusBadge';
import CreateApplicationModal from '../components/CreateApplicationModal';
import { dashboardService, applicationService, emailService } from '../services/api';
import { Briefcase, Clock, MessageSquare, Calendar, CheckCircle2, Plus, ArrowRight, RefreshCw } from 'lucide-react';

const Dashboard = () => {
  const [stats, setStats] = useState({
    total_applications: 0,
    waiting_for_response: 0,
    hr_replies: 0,
    scheduled_followups: 0,
    completed_applications: 0,
  });
  const [recentApps, setRecentApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsData, appsData] = await Promise.all([
        dashboardService.getStats(),
        applicationService.getApplications()
      ]);
      setStats(statsData);
      setRecentApps(appsData.slice(0, 5));
    } catch (err) {
      console.error('Failed to fetch dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSyncInbox = async () => {
    setSyncing(true);
    try {
      await emailService.syncInbox();
      await fetchData();
    } catch (err) {
      console.error(err);
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const statCards = [
    { title: 'Total Applications', count: stats.total_applications, icon: Briefcase, color: 'text-blue-600', bg: 'bg-blue-50' },
    { title: 'Waiting for Response', count: stats.waiting_for_response, icon: Clock, color: 'text-amber-600', bg: 'bg-amber-50' },
    { title: 'HR Replies', count: stats.hr_replies, icon: MessageSquare, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { title: 'Scheduled Follow-ups', count: stats.scheduled_followups, icon: Calendar, color: 'text-purple-600', bg: 'bg-purple-50' },
    { title: 'Completed Applications', count: stats.completed_applications, icon: CheckCircle2, color: 'text-slate-600', bg: 'bg-slate-100' },
  ];

  return (
    <Layout>
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Dashboard Overview</h1>
            <p className="text-sm text-slate-500 mt-1">Monitor job application response status and AI follow-up schedules</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleSyncInbox}
              disabled={syncing}
              className="flex items-center space-x-2 px-4 py-2.5 bg-slate-100 text-slate-700 font-semibold text-sm rounded-xl hover:bg-slate-200 transition-colors border border-slate-200"
            >
              <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin text-blue-600' : ''}`} />
              <span>{syncing ? 'Syncing...' : 'Sync Gmail Inbox'}</span>
            </button>
            <button
              onClick={() => setIsModalOpen(true)}
              className="flex items-center space-x-2 px-4 py-2.5 bg-blue-600 text-white font-semibold text-sm rounded-xl hover:bg-blue-700 transition-colors shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>New Application</span>
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {statCards.map((card, idx) => {
            const Icon = card.icon;
            return (
              <div key={idx} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-slate-500 uppercase">{card.title}</span>
                  <div className={`p-2 rounded-xl ${card.bg}`}>
                    <Icon className={`w-5 h-5 ${card.color}`} />
                  </div>
                </div>
                <div className="text-3xl font-black text-slate-900">{loading ? '-' : card.count}</div>
              </div>
            );
          })}
        </div>

        {/* Recent Applications Section */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-6 border-b border-slate-200 flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900">Recent Job Applications</h2>
            <Link to="/applications" className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-1">
              <span>View All Applications</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-slate-500 text-xs font-semibold uppercase tracking-wider border-b border-slate-200">
                  <th className="py-3.5 px-6">Company & Role</th>
                  <th className="py-3.5 px-6">HR Contact</th>
                  <th className="py-3.5 px-6">Application Date</th>
                  <th className="py-3.5 px-6">Follow-ups</th>
                  <th className="py-3.5 px-6">Status</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {recentApps.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      {loading ? 'Loading applications...' : 'No applications found. Click "New Application" to add one!'}
                    </td>
                  </tr>
                ) : (
                  recentApps.map((app) => (
                    <tr key={app.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-4 px-6">
                        <div className="font-bold text-slate-900">{app.company}</div>
                        <div className="text-xs text-slate-500">{app.job_title}</div>
                      </td>
                      <td className="py-4 px-6 text-slate-700 font-medium">
                        {app.contact?.name || 'HR Team'}
                      </td>
                      <td className="py-4 px-6 text-slate-500 text-xs font-medium">
                        {new Date(app.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-4 px-6 text-slate-700 font-semibold">
                        {app.followup_count} sent
                      </td>
                      <td className="py-4 px-6">
                        <StatusBadge status={app.status} />
                      </td>
                      <td className="py-4 px-6 text-right">
                        <Link
                          to={`/applications/${app.id}`}
                          className="text-xs font-semibold text-blue-600 hover:underline"
                        >
                          Details →
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <CreateApplicationModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSuccess={fetchData}
        />
      </div>
    </Layout>
  );
};

export default Dashboard;

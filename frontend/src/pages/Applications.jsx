import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import StatusBadge from '../components/StatusBadge';
import CreateApplicationModal from '../components/CreateApplicationModal';
import { applicationService } from '../services/api';
import { Plus, Search, Trash2, Eye } from 'lucide-react';

const Applications = () => {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchApps = async () => {
    setLoading(true);
    try {
      const data = await applicationService.getApplications(statusFilter);
      setApplications(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApps();
  }, [statusFilter]);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this job application?')) {
      try {
        await applicationService.deleteApplication(id);
        fetchApps();
      } catch (err) {
        alert('Failed to delete application.');
      }
    }
  };

  const filteredApps = applications.filter((app) =>
    app.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
    app.job_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (app.contact?.name && app.contact.name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Job Applications</h1>
            <p className="text-sm text-slate-500 mt-1">Manage all your active and past job applications</p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2.5 bg-blue-600 text-white font-semibold text-sm rounded-xl hover:bg-blue-700 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Add Application</span>
          </button>
        </div>

        {/* Filters and Search Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search company, position, HR..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center space-x-2 overflow-x-auto w-full sm:w-auto">
            {['', 'waiting', 'replied', 'follow_up_scheduled', 'closed'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize whitespace-nowrap transition-colors ${
                  statusFilter === st
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {st === '' ? 'All Statuses' : st.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Applications Table */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-slate-500 text-xs font-semibold uppercase tracking-wider border-b border-slate-200">
                  <th className="py-3.5 px-6">Company</th>
                  <th className="py-3.5 px-6">Position</th>
                  <th className="py-3.5 px-6">HR Contact</th>
                  <th className="py-3.5 px-6">Application Date</th>
                  <th className="py-3.5 px-6">Next Follow-up</th>
                  <th className="py-3.5 px-6">Follow-up Count</th>
                  <th className="py-3.5 px-6">Status</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {filteredApps.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-12 text-center text-slate-400">
                      {loading ? 'Loading applications...' : 'No matching applications found.'}
                    </td>
                  </tr>
                ) : (
                  filteredApps.map((app) => (
                    <tr key={app.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-4 px-6 font-bold text-slate-900">{app.company}</td>
                      <td className="py-4 px-6 font-medium text-slate-800">{app.job_title}</td>
                      <td className="py-4 px-6 text-slate-600">
                        <div>{app.contact?.name || 'HR Team'}</div>
                        <div className="text-xs text-slate-400">{app.contact?.email}</div>
                      </td>
                      <td className="py-4 px-6 text-slate-500 text-xs font-medium">
                        {new Date(app.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-4 px-6 text-slate-600 text-xs font-medium">
                        {app.next_followup_at ? new Date(app.next_followup_at).toLocaleString() : 'None scheduled'}
                      </td>
                      <td className="py-4 px-6 font-semibold text-slate-700">
                        {app.followup_count}
                      </td>
                      <td className="py-4 px-6">
                        <StatusBadge status={app.status} />
                      </td>
                      <td className="py-4 px-6 text-right space-x-2">
                        <Link
                          to={`/applications/${app.id}`}
                          className="inline-flex items-center p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="View Application Details"
                        >
                          <Eye className="w-4 h-4" />
                        </Link>
                        <button
                          onClick={(e) => handleDelete(app.id, e)}
                          className="inline-flex items-center p-1.5 text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                          title="Delete Application"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
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
          onSuccess={fetchApps}
        />
      </div>
    </Layout>
  );
};

export default Applications;

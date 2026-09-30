import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import StatusBadge from '../components/StatusBadge';
import { emailService } from '../services/api';
import { Mail, Search, RefreshCw, ArrowRight, User, Building, Calendar, Inbox, CheckCircle2 } from 'lucide-react';

const Emails = () => {
  const [emails, setEmails] = useState([]);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [typeFilter, setTypeFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchEmails = async () => {
    setLoading(true);
    try {
      const data = await emailService.getAllEmails(typeFilter);
      setEmails(data);
      if (data.length > 0 && !selectedEmail) {
        setSelectedEmail(data[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmails();
  }, [typeFilter]);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await emailService.syncInbox();
      await fetchEmails();
    } catch (err) {
      console.error(err);
    } finally {
      setSyncing(false);
    }
  };

  const filteredEmails = emails.filter((e) =>
    e.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.sender.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.receiver.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.body.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2">
              <Inbox className="w-6 h-6 text-blue-600" />
              <span>All Emails & Conversation Messages</span>
            </h1>
            <p className="text-sm text-slate-500 mt-1">View all synced initial application emails, HR replies, and follow-up messages</p>
          </div>

          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center space-x-2 px-4 py-2.5 bg-slate-900 text-white font-semibold text-sm rounded-xl hover:bg-slate-800 transition-colors shadow-sm self-start sm:self-auto"
          >
            <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin text-blue-400' : ''}`} />
            <span>{syncing ? 'Syncing...' : 'Sync Gmail Inbox'}</span>
          </button>
        </div>

        {/* Filters and Search Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search subject, sender, company..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center space-x-2 overflow-x-auto w-full sm:w-auto">
            {[
              { id: '', label: 'All Emails' },
              { id: 'initial', label: 'Initial Sent' },
              { id: 'reply', label: 'HR Replies' },
              { id: 'follow_up', label: 'Follow-ups' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setTypeFilter(tab.id)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
                  typeFilter === tab.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Split View: Left List, Right Reader */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[600px]">
          {/* Left Column: Email List */}
          <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden flex flex-col">
            <div className="p-4 bg-slate-50 border-b border-slate-200 font-bold text-xs uppercase text-slate-500 tracking-wider">
              Email Inbox ({filteredEmails.length})
            </div>

            <div className="divide-y divide-slate-100 overflow-y-auto max-h-[650px] flex-1">
              {filteredEmails.length === 0 ? (
                <div className="p-8 text-center text-slate-400">
                  {loading ? 'Loading emails...' : 'No emails found in your inbox.'}
                </div>
              ) : (
                filteredEmails.map((item) => {
                  const isSelected = selectedEmail?.id === item.id;
                  return (
                    <div
                      key={item.id}
                      onClick={() => setSelectedEmail(item)}
                      className={`p-4 cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-blue-50/70 border-l-4 border-blue-600'
                          : 'hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-bold text-slate-900 text-sm truncate max-w-[200px]">
                          {item.company}
                        </span>
                        <StatusBadge status={item.email_type} />
                      </div>

                      <div className="text-xs font-semibold text-slate-800 mb-1 truncate">
                        {item.subject}
                      </div>

                      <div className="text-xs text-slate-500 line-clamp-2 mb-2">
                        {item.body}
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium">
                        <span>From: {item.sender.split('<')[0]}</span>
                        <span>{new Date(item.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Right Column: Full Email Content Reader */}
          <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 shadow-xs p-6 flex flex-col justify-between">
            {selectedEmail ? (
              <div className="space-y-6 flex-1">
                <div className="border-b border-slate-200 pb-4 space-y-3">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <StatusBadge status={selectedEmail.email_type} />
                    <span className="text-xs text-slate-400 font-semibold">
                      {new Date(selectedEmail.sent_at || selectedEmail.created_at).toLocaleString()}
                    </span>
                  </div>

                  <h2 className="text-xl font-bold text-slate-900">{selectedEmail.subject}</h2>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs bg-slate-50 p-3 rounded-xl border border-slate-100">
                    <div>
                      <span className="font-semibold text-slate-500">From:</span>{' '}
                      <span className="font-medium text-slate-800">{selectedEmail.sender}</span>
                    </div>
                    <div>
                      <span className="font-semibold text-slate-500">To:</span>{' '}
                      <span className="font-medium text-slate-800">{selectedEmail.receiver}</span>
                    </div>
                    <div>
                      <span className="font-semibold text-slate-500">Company:</span>{' '}
                      <span className="font-bold text-slate-900">{selectedEmail.company}</span>
                    </div>
                    <div>
                      <span className="font-semibold text-slate-500">Position:</span>{' '}
                      <span className="font-medium text-slate-800">{selectedEmail.job_title}</span>
                    </div>
                  </div>
                </div>

                {/* Email Body Reader */}
                <div>
                  <div className="text-xs font-bold uppercase text-slate-400 tracking-wider mb-2">Message Content</div>
                  <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5 text-sm text-slate-800 font-sans whitespace-pre-wrap leading-relaxed shadow-inner">
                    {selectedEmail.body}
                  </div>
                </div>

                {/* Direct link to Application Details */}
                {selectedEmail.application_id && (
                  <div className="pt-4 border-t border-slate-200 flex justify-end">
                    <Link
                      to={`/applications/${selectedEmail.application_id}`}
                      className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white font-semibold text-xs rounded-xl hover:bg-blue-700 transition-colors"
                    >
                      <span>View Full Application Timeline</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-24 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
                <Mail className="w-12 h-12 text-slate-300" />
                <p className="text-sm font-semibold">Select an email from the inbox list to read full content</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Emails;

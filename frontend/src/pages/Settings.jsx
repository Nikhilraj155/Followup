import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { settingsService } from '../services/api';
import { Settings as SettingsIcon, Save, Sparkles, Shield, Clock, CheckCircle2, AlertCircle } from 'lucide-react';

const Settings = () => {
  const [firstIntervalHours, setFirstIntervalHours] = useState(24);
  const [firstStageFollowups, setFirstStageFollowups] = useState(3);
  const [secondIntervalDays, setSecondIntervalDays] = useState(5);
  const [maximumFollowups, setMaximumFollowups] = useState(4);
  const [autoSend, setAutoSend] = useState(false);
  const [requireApproval, setRequireApproval] = useState(true);
  const [aiEnabled, setAiEnabled] = useState(true);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const data = await settingsService.getSettings();
      setFirstIntervalHours(data.first_interval_hours);
      setFirstStageFollowups(data.first_stage_followups);
      setSecondIntervalDays(data.second_interval_days);
      setMaximumFollowups(data.maximum_followups);
      setAutoSend(data.auto_send);
      setRequireApproval(data.require_approval);
      setAiEnabled(data.ai_enabled);
    } catch (err) {
      console.error(err);
      setMessage({ type: 'error', text: 'Failed to load automation settings.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage({ type: '', text: '' });

    try {
      await settingsService.updateSettings({
        first_interval_hours: parseInt(firstIntervalHours),
        first_stage_followups: parseInt(firstStageFollowups),
        second_interval_days: parseInt(secondIntervalDays),
        maximum_followups: parseInt(maximumFollowups),
        auto_send: autoSend,
        require_approval: requireApproval,
        ai_enabled: aiEnabled
      });
      setMessage({ type: 'success', text: 'Automation rules saved successfully!' });
    } catch (err) {
      console.error(err);
      setMessage({ type: 'error', text: 'Failed to save settings.' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="py-12 text-center text-slate-500">Loading automation settings...</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl space-y-6">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Automation & AI Settings</h1>
          <p className="text-sm text-slate-500 mt-1">Configure automated follow-up intervals, stage delays, and AI approval behavior</p>
        </div>

        {message.text && (
          <div className={`p-4 rounded-xl text-sm font-semibold flex items-center space-x-2 border ${
            message.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}>
            {message.type === 'success' ? <CheckCircle2 className="w-5 h-5 text-emerald-600" /> : <AlertCircle className="w-5 h-5 text-rose-600" />}
            <span>{message.text}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Stage 1 & Stage 2 Intervals */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
              <Clock className="w-5 h-5 text-blue-600" />
              <span>Follow-up Cadence & Delay Rules</span>
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Initial Stage Delay (Hours)
                </label>
                <input
                  type="number"
                  min={1}
                  value={firstIntervalHours}
                  onChange={(e) => setFirstIntervalHours(e.target.value)}
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-semibold focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                <p className="text-xs text-slate-500 mt-1">Wait duration before initial follow-ups (default: 24h)</p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  First-Stage Follow-up Count
                </label>
                <input
                  type="number"
                  min={1}
                  value={firstStageFollowups}
                  onChange={(e) => setFirstStageFollowups(e.target.value)}
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-semibold focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                <p className="text-xs text-slate-500 mt-1">Number of follow-ups in stage 1 (default: 3)</p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Second-Stage Delay (Days)
                </label>
                <input
                  type="number"
                  min={1}
                  value={secondIntervalDays}
                  onChange={(e) => setSecondIntervalDays(e.target.value)}
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-semibold focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                <p className="text-xs text-slate-500 mt-1">Switch waiting period for final stage (default: 5 days)</p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Maximum Total Follow-ups Limit
                </label>
                <input
                  type="number"
                  min={1}
                  value={maximumFollowups}
                  onChange={(e) => setMaximumFollowups(e.target.value)}
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-semibold focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                <p className="text-xs text-slate-500 mt-1">Hard cap on total follow-ups per application (default: 4)</p>
              </div>
            </div>
          </div>

          {/* AI & Approval Controls */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
              <Shield className="w-5 h-5 text-indigo-600" />
              <span>Approval & AI Generation Controls</span>
            </h2>

            <div className="space-y-4 pt-2">
              <label className="flex items-start space-x-3 cursor-pointer p-3 rounded-xl border border-slate-100 hover:bg-slate-50 transition-colors">
                <input
                  type="checkbox"
                  checked={aiEnabled}
                  onChange={(e) => setAiEnabled(e.target.checked)}
                  className="w-5 h-5 text-blue-600 rounded-md mt-0.5"
                />
                <div>
                  <div className="text-sm font-bold text-slate-900 flex items-center space-x-1.5">
                    <Sparkles className="w-4 h-4 text-amber-500" />
                    <span>AI-Generated Follow-ups ON</span>
                  </div>
                  <div className="text-xs text-slate-500">Automatically compose personalized messages using LLM API based on original application context</div>
                </div>
              </label>

              <label className="flex items-start space-x-3 cursor-pointer p-3 rounded-xl border border-slate-100 hover:bg-slate-50 transition-colors">
                <input
                  type="checkbox"
                  checked={requireApproval}
                  onChange={(e) => setRequireApproval(e.target.checked)}
                  className="w-5 h-5 text-blue-600 rounded-md mt-0.5"
                />
                <div>
                  <div className="text-sm font-bold text-slate-900">User Approval Required ON (Recommended)</div>
                  <div className="text-xs text-slate-500">Save AI generated messages as drafts in the dashboard for human review before sending</div>
                </div>
              </label>

              <label className="flex items-start space-x-3 cursor-pointer p-3 rounded-xl border border-slate-100 hover:bg-slate-50 transition-colors">
                <input
                  type="checkbox"
                  checked={autoSend}
                  onChange={(e) => setAutoSend(e.target.checked)}
                  className="w-5 h-5 text-blue-600 rounded-md mt-0.5"
                />
                <div>
                  <div className="text-sm font-bold text-slate-900">Automatic Dispatch ON</div>
                  <div className="text-xs text-slate-500">Bypass manual review and automatically send follow-up emails when delay expires</div>
                </div>
              </label>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white font-bold text-sm rounded-xl hover:bg-blue-700 transition-colors shadow-md"
            >
              <Save className="w-4 h-4" />
              <span>{saving ? 'Saving Settings...' : 'Save Automation Rules'}</span>
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
};

export default Settings;

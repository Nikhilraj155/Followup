import React, { useState } from 'react';
import { X, Paperclip, Send, Save, AlertCircle } from 'lucide-react';
import { applicationService, emailService } from '../services/api';

const CreateApplicationModal = ({ isOpen, onClose, onSuccess }) => {
  const [hrEmail, setHrEmail] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [resume, setResume] = useState(null);
  const [sendNow, setSendNow] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Auto-derive company, job_title, and hr_name if omitted
    const emailPrefix = hrEmail.split('@')[0] || 'HR';
    const domain = hrEmail.split('@')[1] ? hrEmail.split('@')[1].split('.')[0] : 'Company';
    const derivedCompany = domain.charAt(0).toUpperCase() + domain.slice(1);
    const derivedHrName = emailPrefix.replace(/[^a-zA-Z]/g, ' ').trim().toUpperCase() || 'HR Team';
    const derivedJobTitle = subject ? subject.replace(/^(Application for|Re:|Fwd:)\s*/i, '').trim() : 'Job Position';

    try {
      if (sendNow) {
        // Send email with resume attachment via /api/emails/send
        const formData = new FormData();
        formData.append('company', derivedCompany);
        formData.append('job_title', derivedJobTitle);
        formData.append('hr_name', derivedHrName);
        formData.append('hr_email', hrEmail);
        formData.append('subject', subject);
        formData.append('body', body);
        if (resume) {
          formData.append('resume', resume);
        }

        await emailService.sendApplicationEmail(formData);
      } else {
        // Save application record via /api/applications
        await applicationService.createApplication({
          company: derivedCompany,
          job_title: derivedJobTitle,
          hr_name: derivedHrName,
          hr_email: hrEmail,
          subject: subject,
          initial_email_body: body
        });
      }

      onSuccess();
      onClose();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to send email.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl max-w-xl w-full shadow-2xl overflow-hidden border border-slate-200">
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <h2 className="text-lg font-bold">Write Email & Apply</h2>
          <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs font-semibold flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">HR Email Address *</label>
            <input
              type="email"
              required
              placeholder="recruiter@company.com"
              value={hrEmail}
              onChange={(e) => setHrEmail(e.target.value)}
              className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Subject *</label>
            <input
              type="text"
              required
              placeholder="Application for Software Developer"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Email Body *</label>
            <textarea
              rows={6}
              required
              placeholder="Dear HR Team, I am applying for the position..."
              value={body}
              onChange={(e) => setBody(e.target.value)}
              className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none font-sans"
            />
          </div>

          {/* File attachment */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Attach Resume (PDF/DOCX)</label>
            <div className="flex items-center space-x-3">
              <label className="flex items-center space-x-2 px-4 py-2 border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-50 cursor-pointer transition-colors">
                <Paperclip className="w-4 h-4 text-slate-500" />
                <span>{resume ? resume.name : 'Choose File'}</span>
                <input
                  type="file"
                  accept=".pdf,.docx,.doc"
                  onChange={(e) => setResume(e.target.files[0])}
                  className="hidden"
                />
              </label>
              {resume && (
                <button
                  type="button"
                  onClick={() => setResume(null)}
                  className="text-xs text-rose-600 font-semibold hover:underline"
                >
                  Remove
                </button>
              )}
            </div>
          </div>

          {/* Action selection */}
          <div className="pt-3 border-t border-slate-200 flex items-center justify-between">
            <label className="flex items-center space-x-2 text-xs font-semibold text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={sendNow}
                onChange={(e) => setSendNow(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded-xs focus:ring-blue-500"
              />
              <span>Send email immediately</span>
            </label>

            <div className="flex space-x-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl text-xs font-semibold hover:bg-slate-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex items-center space-x-2 px-5 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700 transition-colors shadow-sm"
              >
                {sendNow ? <Send className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
                <span>{loading ? 'Sending...' : sendNow ? 'Send & Track' : 'Save Email'}</span>
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateApplicationModal;

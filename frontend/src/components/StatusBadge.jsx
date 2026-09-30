import React from 'react';

const StatusBadge = ({ status }) => {
  const getBadgeStyle = (st) => {
    switch (st?.toLowerCase()) {
      case 'replied':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'follow_up_scheduled':
      case 'scheduled':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'waiting':
      case 'sent':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'draft':
      case 'generating':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'approved':
        return 'bg-indigo-100 text-indigo-800 border-indigo-200';
      case 'closed':
      case 'cancelled':
      case 'skipped':
        return 'bg-slate-100 text-slate-700 border-slate-200';
      case 'failed':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const formatText = (st) => {
    if (!st) return 'Unknown';
    return st.replace(/_/g, ' ').toUpperCase();
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getBadgeStyle(
        status
      )}`}
    >
      {formatText(status)}
    </span>
  );
};

export default StatusBadge;

import React from 'react';
import { StatusType } from '../types';

interface StatusBadgeProps {
  status: StatusType;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const getStatusStyles = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
      case 'healthy':
      case 'success':
      case 'pass':
        return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
      case 'error':
      case 'failed':
      case 'fail':
      case 'critical':
        return 'bg-rose-500/10 text-rose-500 border-rose-500/20';
      case 'pending':
      case 'warning':
        return 'bg-amber-500/10 text-amber-500 border-amber-500/20';
      default:
        return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
    }
  };

  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getStatusStyles(status)}`}>
      {status}
    </span>
  );
};

export default StatusBadge;

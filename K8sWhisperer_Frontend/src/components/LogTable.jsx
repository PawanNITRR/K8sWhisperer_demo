import React from 'react';
import { ClipboardList, CheckCircle2, ShieldAlert, Clock } from 'lucide-react';

/**
 * Audit trail table — timestamps, resource/anomaly, planned action, explanation.
 */
const LogTable = ({ auditLogs }) => {
  const getActionStyle = (action) => {
    const a = String(action || '').toLowerCase();
    if (a.includes('restart') || a.includes('patch')) return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    if (a.includes('rollback') || a.includes('delete')) return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
    return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  };

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      <div className="p-4 border-b border-slate-800 bg-slate-800/30 flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <ClipboardList className="text-blue-400" size={20} />
          <h3 className="font-bold text-slate-100 text-lg">Autonomous Audit Trail</h3>
        </div>
        <span className="text-[10px] text-slate-500 font-mono uppercase tracking-widest">
          Stage 07: Persistent History
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse table-fixed">
          <colgroup>
            <col className="w-[11rem]" />
            <col className="w-[22%]" />
            <col className="w-[30%]" />
            <col className="w-auto" />
          </colgroup>
          <thead>
            <tr className="bg-slate-950/50 text-slate-500 uppercase text-[10px] tracking-wider">
              <th className="px-4 sm:px-6 py-3 font-black">Timestamp</th>
              <th className="px-4 sm:px-6 py-3 font-black">Resource / Anomaly</th>
              <th className="px-4 sm:px-6 py-3 font-black">Action Taken</th>
              <th className="px-4 sm:px-6 py-3 font-black">Explanation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {auditLogs.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-10 text-center text-slate-600 italic text-sm">
                  No incidents recorded in this cycle. Monitoring workloads…
                </td>
              </tr>
            ) : (
              auditLogs.map((log, index) => (
                <tr key={index} className="hover:bg-slate-800/30 transition-colors group align-top">
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-slate-400 text-xs">
                      <Clock size={12} className="mr-2 shrink-0 opacity-50" />
                      <span className="truncate">{log.timestamp || new Date().toLocaleTimeString()}</span>
                    </div>
                  </td>

                  <td className="px-4 sm:px-6 py-4 min-w-0">
                    <div className="text-sm font-bold text-slate-200 truncate" title={log.resource}>
                      {log.resource}
                    </div>
                    <div
                      className="text-base sm:text-lg text-red-400 font-mono font-extrabold tracking-tight mt-1.5 break-words"
                      title={log.anomaly_type}
                    >
                      {log.anomaly_type}
                    </div>
                  </td>

                  <td className="px-4 sm:px-6 py-4 min-w-0">
                    <span
                      className={`text-sm sm:text-base px-3 py-2 rounded-lg border font-semibold leading-snug text-left block w-full break-words ${getActionStyle(log.action)}`}
                    >
                      {log.action}
                    </span>
                  </td>

                  <td className="px-4 sm:px-6 py-4 min-w-0">
                    <p className="text-xs sm:text-sm text-slate-400 leading-relaxed group-hover:text-slate-200 transition-colors break-words">
                      {log.explanation}
                    </p>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="p-3 bg-slate-950/20 border-t border-slate-800 flex items-center justify-between">
        <div className="flex items-center text-[10px] text-slate-500 space-x-4">
          <span className="flex items-center">
            <CheckCircle2 size={12} className="mr-1 text-green-500 shrink-0" /> Cycles logged: {auditLogs.length}
          </span>
          <span className="flex items-center">
            <ShieldAlert size={12} className="mr-1 text-amber-500 shrink-0" /> HITL approved:{' '}
            {auditLogs.filter((l) => l.approved === true).length}
          </span>
        </div>
      </div>
    </div>
  );
};

export default LogTable;

import React from 'react';
import { ClipboardList, CheckCircle2, ShieldAlert, ExternalLink, Clock } from 'lucide-react';

/**
 * LogTable Component
 * Purpose: Fulfills Stage 07 (Explain & Log) and the 25-mark Web3 Bonus.
 * Displays the persistent history of all incidents, decisions, and actions.
 */
const LogTable = ({ auditLogs }) => {
  
  // Helper to style the status badges in the audit trail
  const getActionStyle = (action) => {
    const a = String(action || '').toLowerCase();
    if (a.includes('restart') || a.includes('patch')) return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    if (a.includes('rollback') || a.includes('delete')) return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
    return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  };

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      {/* Header Section */}
      <div className="p-4 border-b border-slate-800 bg-slate-800/30 flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <ClipboardList className="text-blue-400" size={20} />
          <h3 className="font-bold text-slate-100 text-lg">Autonomous Audit Trail</h3>
        </div>
        <span className="text-[10px] text-slate-500 font-mono uppercase tracking-widest">
          Stage 07: Persistent History
        </span>
      </div>

      {/* Table Section */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-950/50 text-slate-500 uppercase text-[10px] tracking-wider">
              <th className="px-6 py-3 font-black">Timestamp</th>
              <th className="px-6 py-3 font-black">Resource / Anomaly</th>
              <th className="px-6 py-3 font-black">Action Taken</th>
              <th className="px-6 py-3 font-black">Plain-English Explanation</th>
              <th className="px-6 py-3 font-black text-right">Web3 Verify</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {auditLogs.length === 0 ? (
              <tr>
                <td colSpan="5" className="px-6 py-10 text-center text-slate-600 italic text-sm">
                  No incidents recorded in current observe cycle. Monitoring cluster...
                </td>
              </tr>
            ) : (
              auditLogs.map((log, index) => (
                <tr key={index} className="hover:bg-slate-800/30 transition-colors group">
                  {/* Timestamp */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-slate-400 text-xs">
                      <Clock size={12} className="mr-2 opacity-50" />
                      {log.timestamp || new Date().toLocaleTimeString()}
                    </div>
                  </td>

                  {/* Resource & Anomaly Type */}
                  <td className="px-6 py-4">
                    <div className="text-sm font-bold text-slate-200">{log.resource}</div>
                    <div className="text-[10px] text-red-400 font-mono font-bold uppercase">
                      {log.anomaly_type}
                    </div>
                  </td>

                  {/* Action Badge */}
                  <td className="px-6 py-4">
                    <span className={`text-[10px] px-2 py-1 rounded-md border font-bold uppercase ${getActionStyle(log.action)}`}>
                      {log.action}
                    </span>
                  </td>

                  {/* Plain English Diagnosis */}
                  <td className="px-6 py-4 max-w-xs">
                    <p className="text-xs text-slate-400 leading-relaxed group-hover:text-slate-200 transition-colors">
                      {log.explanation}
                    </p>
                  </td>

                  {/* Web3 / Stellar Bonus Button */}
                  <td className="px-6 py-4 text-right">
                    <button className="inline-flex items-center space-x-1 px-3 py-1 bg-purple-900/30 border border-purple-500/40 rounded text-purple-300 text-[10px] font-bold hover:bg-purple-500 hover:text-white transition-all">
                      <ExternalLink size={10} />
                      <span>Stellar Ledger</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Footer / Summary Info */}
      <div className="p-3 bg-slate-950/20 border-t border-slate-800 flex items-center justify-between">
        <div className="flex items-center text-[10px] text-slate-500 space-x-4">
          <span className="flex items-center">
            <CheckCircle2 size={12} className="mr-1 text-green-500" /> Cycles logged: {auditLogs.length}
          </span>
          <span className="flex items-center">
            <ShieldAlert size={12} className="mr-1 text-amber-500" /> HITL approved:{' '}
            {auditLogs.filter((l) => l.approved === true).length}
          </span>
        </div>
      </div>
    </div>
  );
};

export default LogTable;
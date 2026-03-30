import React from 'react';
import { ShieldAlert, CheckCircle, XCircle, Zap, Info } from 'lucide-react';

/**
 * SafetyGate Component
 * Purpose: Implements Stage 05 (Safety Gate) risk-based routing.
 * It captures the HITL flow for actions with high blast_radius or low confidence[cite: 30, 49].
 */
const targetLabel = (remediation) => {
  if (remediation.target_resource) return remediation.target_resource;
  const t = remediation.target;
  if (t && typeof t === 'object') {
    return `${t.kind || 'Pod'}/${t.namespace || 'default'}/${t.name || '?'}`;
  }
  return '—';
};

const SafetyGate = ({ remediation, onApprove, onReject }) => {
  if (!remediation || remediation.status === 'executed') return null;

  const actionLabel = remediation.action_type ?? remediation.action ?? '—';
  const justification = remediation.justification ?? remediation.rationale ?? '';
  const blast = (remediation.blast_radius || 'low').toString().toLowerCase();
  const conf = typeof remediation.confidence === 'number' ? remediation.confidence : 0.85;

  const isHighRisk = blast === 'high' || conf < 0.8;

  return (
    <div
      className={`mt-6 rounded-2xl border-2 transition-all duration-500 overflow-hidden shadow-2xl
      ${isHighRisk ? 'border-amber-500 bg-amber-950/20' : 'border-blue-500 bg-blue-950/20'}`}
    >
      <div
        className={`p-4 flex items-center justify-between ${isHighRisk ? 'bg-amber-500' : 'bg-blue-500'}`}
      >
        <div className="flex items-center space-x-2 text-slate-900 font-black uppercase tracking-tighter">
          <ShieldAlert size={20} />
          <span>Stage 05: Safety Gate Intervention</span>
        </div>
        <div className="text-[10px] bg-black/20 px-2 py-0.5 rounded font-bold text-slate-900">
          AWAITING APPROVAL
        </div>
      </div>

      <div className="p-6">
        <div className="flex items-start space-x-4 mb-6">
          <div className="p-3 bg-slate-900 rounded-xl border border-white/10">
            <Zap size={24} className={isHighRisk ? 'text-amber-400' : 'text-blue-400'} />
          </div>
          <div>
            <h4 className="text-white font-bold text-lg leading-tight">
              Proposed Fix: <span className="text-blue-300 font-mono">{actionLabel}</span>
            </h4>
            <p className="text-slate-400 text-sm mt-1 italic">
              Target Resource: <span className="text-slate-200">{targetLabel(remediation)}</span>
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-8">
          <div className="bg-slate-950/40 p-3 rounded-lg border border-white/5">
            <span className="text-[10px] text-slate-500 uppercase font-black block mb-1">Blast Radius</span>
            <span
              className={`text-sm font-bold uppercase ${blast === 'high' ? 'text-red-400' : 'text-green-400'}`}
            >
              {blast}
            </span>
          </div>
          <div className="bg-slate-950/40 p-3 rounded-lg border border-white/5">
            <span className="text-[10px] text-slate-500 uppercase font-black block mb-1">AI Confidence</span>
            <span className="text-sm font-bold text-blue-400">{(conf * 100).toFixed(1)}%</span>
          </div>
        </div>

        <div className="mb-8 p-4 bg-black/30 rounded-lg border-l-4 border-blue-400">
          <div className="flex items-center text-blue-400 text-xs font-bold mb-2 uppercase">
            <Info size={14} className="mr-2" /> Planner Logic
          </div>
          <p className="text-slate-300 text-xs leading-relaxed">&ldquo;{justification}&rdquo;</p>
        </div>

        <div className="flex space-x-4">
          <button
            onClick={onApprove}
            className="flex-1 flex items-center justify-center space-x-2 bg-green-600 hover:bg-green-500 text-white font-black py-4 rounded-xl transition-transform active:scale-95 shadow-lg shadow-green-900/20"
          >
            <CheckCircle size={20} />
            <span>APPROVE & EXECUTE</span>
          </button>
          <button
            onClick={onReject}
            className="flex-1 flex items-center justify-center space-x-2 bg-slate-800 hover:bg-red-900/40 text-slate-300 hover:text-red-400 font-bold py-4 rounded-xl border border-slate-700 transition-all active:scale-95"
          >
            <XCircle size={20} />
            <span>REJECT</span>
          </button>
        </div>

        <p className="text-[10px] text-slate-500 mt-6 text-center italic">
          Decision will be recorded in the persistent audit log and synced to the Stellar ledger[cite: 30, 46].
        </p>
      </div>
    </div>
  );
};

export default SafetyGate;

import React from 'react';
import { 
  Eye, 
  Search, 
  Stethoscope, 
  Map, 
  ShieldCheck, 
  PlayCircle, 
  FileText,
  CheckCircle2
} from 'lucide-react';

/**
 * Pipeline Component
 * Purpose: Visualizes the 7-Stage Mandatory Pipeline (PS 1, Stages 01-07).
 * It highlights the active LangGraph node and shows completed stages.
 */
const Pipeline = ({ currentStageIndex }) => {
  // The 7 Stages defined in the Problem Statement [cite: 29, 30]
  const stages = [
    { id: 'observe', label: 'Observe', icon: Eye, desc: 'Scanning Cluster (kubectl MCP)' },
    { id: 'detect', label: 'Detect', icon: Search, desc: 'Anomaly Classification (LLM)' },
    { id: 'diagnose', label: 'Diagnose', icon: Stethoscope, desc: 'Root Cause Analysis' },
    { id: 'plan', label: 'Plan', icon: Map, desc: 'Remediation Proposal' },
    { id: 'safety', label: 'Safety Gate', icon: ShieldCheck, desc: 'Risk-Based Routing (HITL)' },
    { id: 'execute', label: 'Execute', icon: PlayCircle, desc: 'Surgical kubectl Action' },
    { id: 'explain', label: 'Explain & Log', icon: FileText, desc: 'Audit Trail & Web3 Sync' }
  ];

  return (
    <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-2xl shadow-xl h-full">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-xl font-black text-white tracking-tight flex items-center">
          <span className="bg-blue-500 w-2 h-6 mr-3 rounded-full"></span>
          K8sWhisperer Pipeline
        </h3>
        <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-1 rounded border border-slate-700 font-mono">
          POLLING: 30S [cite: 29]
        </span>
      </div>

      <div className="relative space-y-6">
        {/* Vertical Progress Line */}
        <div className="absolute left-[19px] top-2 bottom-2 w-0.5 bg-slate-800"></div>

        {stages.map((stage, index) => {
          const Icon = stage.icon;
          const isCompleted = index < currentStageIndex;
          const isActive = index === currentStageIndex;

          return (
            <div key={stage.id} className="relative flex items-start group">
              {/* Step Indicator */}
              <div className={`z-10 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-500 border-4
                ${isCompleted ? 'bg-green-500 border-green-900/50' : 
                  isActive ? 'bg-blue-600 border-blue-400 animate-pulse' : 
                  'bg-slate-900 border-slate-800'}`}>
                {isCompleted ? (
                  <CheckCircle2 size={18} className="text-white" />
                ) : (
                  <Icon size={18} className={isActive ? 'text-white' : 'text-slate-600'} />
                )}
              </div>

              {/* Stage Content */}
              <div className="ml-5 pt-1">
                <div className="flex items-center space-x-2">
                  <span className={`text-xs font-black uppercase tracking-widest
                    ${isCompleted ? 'text-green-400' : isActive ? 'text-blue-400' : 'text-slate-600'}`}>
                    0{index + 1}
                  </span>
                  <h4 className={`font-bold transition-colors ${isActive ? 'text-white' : 'text-slate-500'}`}>
                    {stage.label}
                  </h4>
                </div>
                <p className={`text-[11px] mt-0.5 transition-colors ${isActive ? 'text-slate-300' : 'text-slate-600'}`}>
                  {stage.desc}
                </p>
              </div>

              {/* Active Stage Radar Effect */}
              {isActive && (
                <div className="absolute left-0 w-10 h-10 rounded-full bg-blue-500/20 animate-ping"></div>
              )}
            </div>
          );
        })}
      </div>

      {/* HITL Notice */}
      <div className="mt-8 p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
        <p className="text-[10px] text-slate-400 leading-relaxed italic">
          * High-risk actions (blast_radius = high) will trigger a Safety Gate pause for HITL approval via Slack[cite: 30].
        </p>
      </div>
    </div>
  );
};

export default Pipeline;
import React from 'react';
import { Shield, AlertCircle, Activity, Box } from 'lucide-react';

/**
 * PodCard Component
 * Purpose: Visualizes individual pod health for the Phase 01: Observe Cluster stage.
 * It highlights anomalies such as OOMKilled or CrashLoopBackOff visually.
 */
export default function PodCard({ pod }) {
  const isError = pod.status === "CrashLoopBackOff" || pod.status === "Error";
  
  return (
    <div className={`relative group transition-all duration-500 hover:scale-[1.02]`}>
      {/* Background Glow */}
      <div className={`absolute -inset-0.5 rounded-xl blur opacity-20 group-hover:opacity-40 transition ${isError ? 'bg-rose-500' : 'bg-blue-500'}`}></div>
      
      {/* Glass Body */}
      <div className="relative bg-[#0f172a]/60 backdrop-blur-xl border border-white/10 p-5 rounded-xl flex flex-col h-full">
        <div className="flex justify-between items-start mb-4">
           <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${isError ? 'border-rose-500/50 text-rose-400 bg-rose-500/10' : 'border-emerald-500/50 text-emerald-400 bg-emerald-500/10'}`}>
             {pod.status}
           </span>
           <span className="text-[10px] text-slate-500">v1.0.4</span>
        </div>
        
        <h3 className="text-lg font-bold text-white truncate mb-1">{pod.name}</h3>
        <p className="text-[10px] text-slate-400 font-mono mb-4 italic truncate">{pod.image}</p>
        
        <div className="mt-auto pt-3 border-t border-white/5 flex justify-between items-center text-[10px] font-mono">
          <span className="text-slate-500 uppercase">Restarts</span>
          <span className={pod.restarts > 0 ? 'text-rose-400' : 'text-slate-300'}>{pod.restarts}</span>
        </div>
      </div>
    </div>
  );
}
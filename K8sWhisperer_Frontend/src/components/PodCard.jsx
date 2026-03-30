import React from 'react';
import { Shield, AlertCircle, Activity, Box } from 'lucide-react';

/**
 * PodCard Component
 * Purpose: Visualizes individual pod health for the Phase 01: Observe Cluster stage.
 * It highlights anomalies such as OOMKilled or CrashLoopBackOff visually.
 */
const PodCard = ({ pod }) => {
  // Determine if the pod has an active anomaly based on status
  // Minimum required: CrashLoopBackOff, OOMKilled, Pending Pod [cite: 41, 42]
  const isAnomalous = ['CrashLoopBackOff', 'OOMKilled', 'Pending', 'ImagePullBackOff', 'Evicted'].includes(pod.status);

  return (
    <div className={`relative overflow-hidden transition-all duration-300 p-4 rounded-xl border-2 
      ${isAnomalous 
        ? 'border-red-500 bg-red-950/30 shadow-[0_0_15px_rgba(239,68,68,0.2)] animate-pulse' 
        : 'border-slate-700 bg-slate-800/50 hover:border-green-500/50'}`}>
      
      {/* Status Header */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center space-x-2">
          <div className={`p-1.5 rounded-lg ${isAnomalous ? 'bg-red-500/20' : 'bg-green-500/20'}`}>
            {isAnomalous ? (
              <AlertCircle size={18} className="text-red-400" />
            ) : (
              <Shield size={18} className="text-green-400" />
            )}
          </div>
          <h4 className="font-bold text-slate-100 truncate max-w-[150px]" title={pod.name}>
            {pod.name}
          </h4>
        </div>
        <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider
          ${isAnomalous ? 'bg-red-500 text-white' : 'bg-green-500/20 text-green-400 border border-green-500/30'}`}>
          {pod.status}
        </span>
      </div>

      {/* Resource Details */}
      <div className="space-y-2 text-xs">
        <div className="flex justify-between text-slate-400">
          <span className="flex items-center">
            <Box size={12} className="mr-1" /> Namespace:
          </span>
          <span className="text-slate-200 font-mono">{pod.namespace}</span>
        </div>
        
        <div className="flex justify-between text-slate-400">
          <span className="flex items-center">
            <Activity size={12} className="mr-1" /> Restarts:
          </span>
          <span className={`font-mono ${pod.restarts > 3 ? 'text-red-400 font-bold' : 'text-slate-200'}`}>
            {pod.restarts}
          </span>
        </div>
      </div>

      {/* Pulse Line for Anomalies */}
      {isAnomalous && (
        <div className="mt-3 pt-2 border-t border-red-500/20">
          <p className="text-[10px] text-red-300 italic font-medium">
            ⚠️ LLM Classifier: High Priority Anomaly 
          </p>
        </div>
      )}

      {/* Background Decoration */}
      <div className={`absolute -right-2 -bottom-2 opacity-10 
        ${isAnomalous ? 'text-red-500' : 'text-slate-500'}`}>
        <Activity size={64} />
      </div>
    </div>
  );
};

export default PodCard;
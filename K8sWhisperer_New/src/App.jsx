import React from 'react';
import useCluster from './hooks/useCluster';
import PodCard from './components/PodCard.jsx';
import Pipeline from './components/Pipeline.jsx';
import LogTable from './components/LogTable.jsx';
import SafetyGate from './components/SafetyGate.jsx';
import { Activity } from 'lucide-react';

export default function App() {
  const {
    pods,
    currentStage,
    loading,
    auditLogs,
    remediation,
    approve,
    reject,
    refresh,
  } = useCluster();

  return (
    <div className="flex h-screen w-full bg-[#020617] overflow-hidden relative">
      
      {/* 1. THE VERTICAL SIDEBAR (Full Height) */}
      <aside className="w-80 h-full bg-white/5 backdrop-blur-xl border-r border-white/10 p-8 flex flex-col shadow-2xl z-20">
        <div className="mb-12 border-b border-white/5 pb-6">
          <h2 className="text-[10px] font-black text-blue-500 uppercase tracking-[0.4em] mb-2">
            Neural Pipeline
          </h2>
          <p className="text-[9px] text-slate-500 font-mono">AGENT_CORE_v2.0</p>
        </div>
        
        {/* Your Pipeline with the new icons and spacing */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          <Pipeline currentStage={currentStage} />
        </div>

        {/* Optional: Bottom Sidebar Info */}
        <div className="mt-auto pt-6 border-t border-white/5 text-[9px] font-mono text-slate-600">
          UPLINK: ACTIVE // CLUSTER: MINIKUBE
        </div>
      </aside>

      {/* 2. THE MAIN CONTENT AREA (Right Side) */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        
        {/* TOP HEADER (Inside the right area) */}
        <header className="h-24 flex justify-between items-center px-10 bg-white/[0.02] border-b border-white/5 backdrop-blur-md">
          <div className="flex items-center space-x-4">
            <div className="p-2 bg-blue-500/20 rounded-lg border border-blue-500/30">
              <Activity className="text-blue-400 w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h1 className="text-2xl font-black tracking-widest text-white italic">
                K8sWHISPERER <span className="text-blue-500 text-lg">v2.0</span>
              </h1>
            </div>
          </div>
          
          <div className="flex items-center space-x-6 text-[10px] font-mono text-slate-500">
            <span className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              <span>SYSTEM_READY</span>
            </span>
          </div>
        </header>

        {/* AUDIT TRAIL / MAIN VIEWPORT */}
        <section className="flex-1 p-10 overflow-y-auto relative">
          <div className="max-w-[90rem] mx-auto space-y-8 px-0">
            {loading && (
              <p className="text-center text-slate-500 text-sm font-mono">Connecting to K8sWhisperer API…</p>
            )}

            {pods.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {pods.map((pod) => (
                  <PodCard key={pod.name} pod={pod} />
                ))}
              </div>
            )}

            <SafetyGate
              remediation={remediation}
              onApprove={() => {
                approve().finally(() => refresh());
              }}
              onReject={() => {
                reject().finally(() => refresh());
              }}
            />

            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-10 shadow-2xl">
              <div className="flex justify-between items-end mb-10 border-b border-white/5 pb-8">
                <div>
                  <h2 className="text-3xl font-black text-white uppercase tracking-tight">Autonomous Audit Trail</h2>
                  <p className="text-[10px] text-blue-400 font-mono tracking-widest uppercase">Stage 07: Persistent History</p>
                </div>
              </div>
              
              <LogTable auditLogs={auditLogs} />
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
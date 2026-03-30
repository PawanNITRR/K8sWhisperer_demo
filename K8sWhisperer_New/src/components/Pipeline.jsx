import React from 'react';
import { Eye, ShieldAlert, Stethoscope, ClipboardList, UserCheck, Play, ScrollText } from 'lucide-react';

const stages = [
  { name: "Observe", icon: Eye },
  { name: "Detect", icon: ShieldAlert },
  { name: "Diagnose", icon: Stethoscope },
  { name: "Plan", icon: ClipboardList },
  { name: "Review", icon: UserCheck }, // This is your Safety Gate/HITL stage
  { name: "Execute", icon: Play },
  { name: "Explain", icon: ScrollText }
];

export default function Pipeline({ currentStage }) {
  return (
    <div className="relative space-y-10 py-4 px-6"> {/* Increased spacing */}
      {/* The Connector Line */}
      <div className="absolute left-[43px] top-0 bottom-0 w-[2px] bg-white/10"></div>
      {stages.map((stage, idx) => {
        const Icon = stage.icon;
        const active = idx === currentStage;
        const past = idx < currentStage;
        
        return (
          <div key={stage.name} className="flex items-center space-x-6 relative group">
            {/* The Node + Icon Wrapper */}
            <div className={`w-10 h-10 rounded-xl border-2 z-10 flex items-center justify-center transition-all duration-700 
              ${active ? 'bg-blue-600 border-blue-300 shadow-[0_0_20px_rgba(59,130,246,0.6)] scale-110' : 
                past ? 'bg-emerald-600 border-emerald-400' : 'bg-slate-900 border-slate-800'}`}>
              
              <Icon size={20} className={`${active || past ? 'text-white' : 'text-slate-600'}`} />
              
              {active && <div className="absolute inset-0 rounded-xl animate-ping bg-blue-400 opacity-20"></div>}
            </div>
            
            {/* Text - Increased size and bolding */}
            <span className={`text-sm font-black uppercase tracking-[0.2em] transition-all duration-500
              ${active ? 'text-blue-400 translate-x-2' : past ? 'text-emerald-400' : 'text-slate-600'}`}>
              {stage.name}
            </span>
          </div>
        );
      })}
    </div>
  );
}
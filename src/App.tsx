import React, { useState } from 'react';
import { 
  BarChart3, 
  ShieldAlert, 
  Grid3X3, 
  Settings, 
  Bell, 
  User,
  Search,
  Command
} from 'lucide-react';
import Dashboard from './components/Dashboard';
import ReportView from './components/ReportView';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const navItems = [
    { id: 'dashboard', label: 'Monitor', icon: <Grid3X3 className="w-5 h-5" /> },
    { id: 'reports', label: 'Security', icon: <ShieldAlert className="w-5 h-5" /> },
    { id: 'analytics', label: 'Analytics', icon: <BarChart3 className="w-5 h-5" /> },
    { id: 'settings', label: 'Settings', icon: <Settings className="w-5 h-5" /> },
  ];

  return (
    <div className="min-h-screen bg-[#0F1113] text-gray-300 flex font-sans">
      {/* Sidebar */}
      <aside className="w-64 border-r border-white/5 flex flex-col hidden lg:flex">
        <div className="p-6 flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-[#F3BA2F] to-[#E2A71E] rounded-lg flex items-center justify-center text-black">
            <Command className="w-5 h-5" />
          </div>
          <span className="text-xl font-bold text-white tracking-tight">K8sWhisperer</span>
        </div>

        <nav className="flex-1 px-4 py-4 space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-medium ${
                activeTab === item.id 
                  ? 'bg-[#F3BA2F]/10 text-[#F3BA2F]' 
                  : 'text-gray-500 hover:bg-white/5 hover:text-white'
              }`}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>

        <div className="p-4 mt-auto">
          <div className="bg-white/5 rounded-2xl p-4 border border-white/5">
            <p className="text-xs font-bold text-gray-400 uppercase mb-2">Cluster Status</p>
            <div className="flex items-center gap-2 text-sm text-white">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Production-Main
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-20 border-b border-white/5 px-8 flex items-center justify-between bg-[#0F1113]/80 backdrop-blur-xl sticky top-0 z-10">
          <div className="flex-1 max-w-xl relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input 
              type="text" 
              placeholder="Search anything... (Ctrl + K)" 
              className="w-full pl-12 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-[#F3BA2F]/50 transition-all"
            />
          </div>

          <div className="flex items-center gap-4">
            <button className="p-2.5 text-gray-400 hover:text-white hover:bg-white/5 rounded-xl transition-all relative">
              <Bell className="w-5 h-5" />
              <span className="absolute top-2 right-2 w-2 h-2 bg-rose-500 rounded-full border-2 border-[#0F1113]" />
            </button>
            <div className="h-8 w-px bg-white/10 mx-2" />
            <button className="flex items-center gap-3 pl-2 pr-1 py-1 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all">
              <span className="text-sm font-medium text-white">Admin User</span>
              <div className="w-8 h-8 bg-gradient-to-tr from-purple-500 to-blue-500 rounded-lg flex items-center justify-center text-white">
                <User className="w-5 h-5" />
              </div>
            </button>
          </div>
        </header>

        {/* Dynamic Content */}
        <div className="p-8 max-w-7xl mx-auto w-full">
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'reports' && <ReportView />}
          {activeTab === 'analytics' && (
            <div className="flex flex-col items-center justify-center py-20 opacity-50">
              <BarChart3 className="w-16 h-16 mb-4" />
              <h2 className="text-xl font-bold">Analytics Coming Soon</h2>
            </div>
          )}
          {activeTab === 'settings' && (
            <div className="flex flex-col items-center justify-center py-20 opacity-50">
              <Settings className="w-16 h-16 mb-4" />
              <h2 className="text-xl font-bold">Settings Panel</h2>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;

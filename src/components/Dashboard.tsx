import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  ShieldCheck, 
  Database, 
  Cpu, 
  Zap, 
  Plus, 
  ArrowUpRight, 
  ArrowDownRight,
  RefreshCw
} from 'lucide-react';
import PortfolioValueChart from './PortfolioValueChart';
import AssetList from './AssetList';
import { Asset } from '../types';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({
    healthScore: 94.2,
    nodesActive: 12,
    uptime: '99.99%',
    riskLevel: 'Low'
  });

  const [assets, setAssets] = useState<Asset[]>([
    { name: 'auth-service-7f5b', type: 'Pod', namespace: 'prod', status: 'Running', lastUpdated: '2m ago' },
    { name: 'payment-gateway', type: 'Deployment', namespace: 'prod', status: 'Healthy', lastUpdated: '5m ago' },
    { name: 'redis-master-0', type: 'Pod', namespace: 'infra', status: 'Running', lastUpdated: '10s ago' },
    { name: 'order-processor', type: 'Pod', namespace: 'prod', status: 'Error', lastUpdated: 'Now' },
    { name: 'api-ingress', type: 'Service', namespace: 'prod', status: 'Healthy', lastUpdated: '1h ago' },
  ]);

  const [isRefreshing, setIsRefreshing] = useState(false);

  const refreshData = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Top Header / Stats Overview */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h2 className="text-gray-400 text-sm font-medium uppercase tracking-[0.2em] mb-1">Overview</h2>
          <div className="flex items-baseline gap-3">
            <h1 className="text-4xl font-bold text-white tracking-tight">Cluster Health</h1>
            <span className="text-emerald-500 flex items-center gap-0.5 text-sm font-semibold">
              <ArrowUpRight className="w-4 h-4" />
              +2.4%
            </span>
          </div>
        </div>
        
        <div className="flex gap-2">
          <button 
            onClick={refreshData}
            className="p-2.5 bg-white/5 border border-white/10 rounded-xl text-gray-400 hover:text-white hover:bg-white/10 transition-all"
          >
            <RefreshCw className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
          <button className="flex items-center gap-2 px-5 py-2.5 bg-[#F3BA2F] hover:bg-[#F3BA2F]/90 text-black font-bold rounded-xl transition-all shadow-lg shadow-[#F3BA2F]/20">
            <Plus className="w-5 h-5" />
            Add Cluster
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Health Score', value: '94.2%', icon: <Activity className="w-5 h-5" />, color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
          { label: 'Active Nodes', value: '12 / 12', icon: <Cpu className="w-5 h-5" />, color: 'text-blue-500', bg: 'bg-blue-500/10' },
          { label: 'Uptime (24h)', value: '99.99%', icon: <Zap className="w-5 h-5" />, color: 'text-[#F3BA2F]', bg: 'bg-[#F3BA2F]/10' },
          { label: 'Risk Profile', value: 'Normal', icon: <ShieldCheck className="w-5 h-5" />, color: 'text-purple-500', bg: 'bg-purple-500/10' },
        ].map((stat, i) => (
          <div key={i} className="bg-[#1A1C1E] p-5 rounded-2xl border border-white/5 flex items-center justify-between group hover:border-white/10 transition-all">
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">{stat.label}</p>
              <p className="text-2xl font-bold text-white tracking-tight">{stat.value}</p>
            </div>
            <div className={`p-3 ${stat.bg} ${stat.color} rounded-xl group-hover:scale-110 transition-transform`}>
              {stat.icon}
            </div>
          </div>
        ))}
      </div>

      {/* Main Grid: Chart & Assets */}
      <div className="grid grid-cols-12 gap-6">
        {/* Chart Column */}
        <div className="col-span-12 xl:col-span-8 bg-[#1A1C1E] p-6 rounded-2xl border border-white/5">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="text-lg font-bold text-white">Performance Index</h3>
              <p className="text-sm text-gray-500">System reliability over the last 24 hours</p>
            </div>
            <div className="flex gap-2 bg-white/5 p-1 rounded-lg">
              {['1H', '1D', '1W', '1M'].map(p => (
                <button key={p} className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${p === '1D' ? 'bg-[#F3BA2F] text-black' : 'text-gray-400 hover:text-white'}`}>
                  {p}
                </button>
              ))}
            </div>
          </div>
          <PortfolioValueChart />
        </div>

        {/* Info Column */}
        <div className="col-span-12 xl:col-span-4 space-y-6">
          <div className="bg-gradient-to-br from-[#F3BA2F] to-[#E2A71E] p-6 rounded-2xl text-black">
            <h3 className="text-lg font-bold mb-1">Smart Alerts</h3>
            <p className="text-sm font-medium opacity-80 mb-4">K8sWhisperer AI has detected 1 critical issue that requires attention.</p>
            <button className="w-full py-3 bg-black text-white font-bold rounded-xl hover:bg-black/90 transition-all flex items-center justify-center gap-2">
              Review and Fix
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
          
          <div className="bg-[#1A1C1E] p-6 rounded-2xl border border-white/5">
            <h3 className="text-lg font-bold text-white mb-4">Quick Actions</h3>
            <div className="grid grid-cols-2 gap-3">
              <button className="p-4 bg-white/2 border border-white/5 rounded-xl hover:bg-white/5 transition-all text-center">
                <Database className="w-6 h-6 text-gray-400 mx-auto mb-2" />
                <span className="text-xs font-bold text-gray-300">Clean Logs</span>
              </button>
              <button className="p-4 bg-white/2 border border-white/5 rounded-xl hover:bg-white/5 transition-all text-center">
                <RefreshCw className="w-6 h-6 text-gray-400 mx-auto mb-2" />
                <span className="text-xs font-bold text-gray-300">Rescale</span>
              </button>
            </div>
          </div>
        </div>

        {/* Full Width Assets Table */}
        <div className="col-span-12">
          <AssetList assets={assets} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

import React from 'react';
import { Box, Server, Database, Activity, Map, ArrowRight } from 'lucide-react';
import StatusBadge from './StatusBadge';
import { Asset } from '../types';

interface AssetListProps {
  assets: Asset[];
}

const AssetList: React.FC<AssetListProps> = ({ assets }) => {
  const getIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'pod': return <Box className="w-5 h-5" />;
      case 'deployment': return <Map className="w-5 h-5" />;
      case 'service': return <Server className="w-5 h-5" />;
      case 'persistentvolumeclaim': return <Database className="w-5 h-5" />;
      default: return <Activity className="w-5 h-5" />;
    }
  };

  return (
    <div className="bg-[#1A1C1E] rounded-xl border border-white/5 overflow-hidden">
      <div className="p-4 border-b border-white/5 flex justify-between items-center">
        <h3 className="text-lg font-semibold text-white">Cluster Resources</h3>
        <button className="text-[#F3BA2F] hover:text-[#f3ba2f]/80 text-sm font-medium transition-colors">
          View All
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead className="bg-white/2 text-gray-400 text-xs font-medium uppercase tracking-wider">
            <tr>
              <th className="px-6 py-3">Resource</th>
              <th className="px-6 py-3">Type</th>
              <th className="px-6 py-3">Namespace</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {assets.map((asset) => (
              <tr 
                key={`${asset.namespace}-${asset.name}`} 
                className="hover:bg-white/[0.02] transition-colors group"
              >
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-white/5 rounded-lg text-gray-400 group-hover:text-[#F3BA2F] transition-colors">
                      {getIcon(asset.type)}
                    </div>
                    <span className="text-white font-medium">{asset.name}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-gray-400">{asset.type}</td>
                <td className="px-6 py-4 text-gray-400">{asset.namespace}</td>
                <td className="px-6 py-4">
                  <StatusBadge status={asset.status} />
                </td>
                <td className="px-6 py-4 text-right">
                  <button className="p-2 hover:bg-white/5 rounded-lg text-gray-400 hover:text-white transition-colors">
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AssetList;

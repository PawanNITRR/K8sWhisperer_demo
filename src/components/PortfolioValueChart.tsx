import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const data = [
  { time: '00:00', health: 98 },
  { time: '04:00', health: 95 },
  { time: '08:00', health: 85 },
  { time: '12:00', health: 92 },
  { time: '16:00', health: 88 },
  { time: '20:00', health: 94 },
  { time: '23:59', health: 99 },
];

const PortfolioValueChart: React.FC = () => {
  return (
    <div className="h-[300px] w-full mt-4">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorHealth" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#F3BA2F" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#F3BA2F" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
          <XAxis 
            dataKey="time" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: '#666', fontSize: 12 }}
            dy={10}
          />
          <YAxis 
            hide={true}
            domain={[0, 100]}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1A1C1E', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
            itemStyle={{ color: '#F3BA2F' }}
          />
          <Area 
            type="monotone" 
            dataKey="health" 
            stroke="#F3BA2F" 
            strokeWidth={3}
            fillOpacity={1} 
            fill="url(#colorHealth)" 
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PortfolioValueChart;

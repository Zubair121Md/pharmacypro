import React from 'react';
import { Box } from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

function aggregateTopN(data, opts) {
  const { nameKey, valueKey, xKey, yKey, topN = 20 } = opts;
  if (!data || data.length <= topN) return data;
  const key = nameKey || xKey;
  const val = valueKey || yKey || 'revenue';
  const sorted = [...data].sort((a, b) => (b[val] || 0) - (a[val] || 0));
  const head = sorted.slice(0, topN);
  const tail = sorted.slice(topN);
  const othersValue = tail.reduce((sum, item) => sum + (item[val] || 0), 0);
  const others = { [key]: 'Others', [val]: othersValue };
  return [...head, others];
}

function RevenueChart({ data, type, xKey, yKey, nameKey, valueKey, height = 300, topN = 20, autoScale = true }) {
  if (!data || data.length === 0) {
    return (
      <Box
        display="flex"
        alignItems="center"
        justifyContent="center"
        height={height}
        color="text.secondary"
      >
        No data available
      </Box>
    );
  }

  const tooManySeries = data.length > topN;
  const processed = autoScale ? aggregateTopN(data, { nameKey, valueKey, xKey, yKey, topN }) : data;
  const dynamicHeight = autoScale && data.length > 10 ? Math.max(height, 600) : height;
  const pieRadius = autoScale ? (data.length > 20 ? 200 : data.length > 10 ? 160 : 120) : 100;

  const renderChart = () => {
    switch (type) {
      case 'bar':
        return (
          <BarChart data={processed} margin={{ top: 5, right: 30, left: 20, bottom: 100 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey={xKey} 
              angle={-45}
              textAnchor="end"
              height={100}
              interval={0}
              tick={{ fontSize: 12 }}
            />
            <YAxis />
            <Tooltip formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, 'Revenue']} />
            <Bar dataKey={yKey} fill="#8884d8" />
          </BarChart>
        );
      
      case 'pie':
        // If too many series, aggregation already applied. Increase radius for readability.
        return (
          <PieChart>
            <Pie
              data={processed}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ payload, percent }) => {
                const key = nameKey || 'name';
                return `${payload[key]} ${(percent * 100).toFixed(0)}%`;
              }}
              outerRadius={pieRadius}
              fill="#8884d8"
              dataKey={valueKey}
            >
              {processed.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, 'Revenue']} />
          </PieChart>
        );
      
      case 'line':
        return (
          <LineChart data={processed} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} />
            <YAxis />
            <Tooltip formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, 'Revenue']} />
            <Line type="monotone" dataKey={yKey} stroke="#8884d8" strokeWidth={2} />
          </LineChart>
        );
      
      default:
        return null;
    }
  };

  return (
    <ResponsiveContainer width="100%" height={dynamicHeight}>
      {renderChart()}
    </ResponsiveContainer>
  );
}

export default RevenueChart;

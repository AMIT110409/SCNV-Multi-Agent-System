import React from 'react';
import { Handle, Position } from 'reactflow';
import { Warehouse } from 'lucide-react';

const DCNode = ({ data, isConnectable }) => {
  return (
    <div style={{
      background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
      padding: '12px 16px',
      borderRadius: '8px',
      color: 'white',
      border: '2px solid #1d4ed8',
      boxShadow: '0 4px 6px -1px rgba(59, 130, 246, 0.4), 0 2px 4px -1px rgba(59, 130, 246, 0.2)',
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      minWidth: '180px'
    }}>
      <Handle type="target" position={Position.Left} isConnectable={isConnectable} style={{ background: '#fff', width: '8px', height: '8px' }} />
      <div style={{ background: 'rgba(255,255,255,0.2)', padding: '8px', borderRadius: '6px' }}>
        <Warehouse size={20} />
      </div>
      <div>
        <div style={{ fontSize: '14px', fontWeight: 'bold', textTransform: 'capitalize' }}>{data.label}</div>
        <div style={{ fontSize: '10px', opacity: 0.8, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{data.type}</div>
      </div>
      <Handle type="source" position={Position.Right} isConnectable={isConnectable} style={{ background: '#fff', width: '8px', height: '8px' }} />
    </div>
  );
};

export default DCNode;

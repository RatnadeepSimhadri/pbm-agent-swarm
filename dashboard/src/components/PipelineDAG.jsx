import { useMemo } from 'react';
import { ReactFlow, Background } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { motion } from 'framer-motion';

const STATUS_STYLES = {
  queued: { bg: '#ffffff', border: '#e5e7eb', text: '#9ca3af', label: '#6b7280' },
  assigned: { bg: '#eff6ff', border: '#93c5fd', text: '#3b82f6', label: '#1d4ed8' },
  in_progress: { bg: '#eff6ff', border: '#3b82f6', text: '#3b82f6', label: '#1d4ed8' },
  waiting_approval: { bg: '#fffbeb', border: '#f59e0b', text: '#f59e0b', label: '#b45309' },
  done: { bg: '#f0fdf4', border: '#86efac', text: '#22c55e', label: '#15803d' },
  failed: { bg: '#fef2f2', border: '#fca5a5', text: '#ef4444', label: '#b91c1c' },
};

const AGENT_LABELS = {
  pm: 'Product Manager',
  tech_lead: 'Tech Lead',
  architect: 'Architect',
  backend_dev: 'Backend Dev',
  frontend_dev: 'Frontend Dev',
  qa: 'QA Engineer',
  deployer: 'Deployer',
};

function AgentNode({ data }) {
  const status = data.status || 'queued';
  const s = STATUS_STYLES[status];
  const isActive = status === 'in_progress' || status === 'waiting_approval';

  return (
    <motion.div
      animate={isActive ? {
        boxShadow: [
          `0 0 0px 0px ${s.border}00`,
          `0 0 12px 4px ${s.border}40`,
          `0 0 0px 0px ${s.border}00`,
        ],
      } : { boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}
      transition={isActive ? { duration: 2, repeat: Infinity } : {}}
      style={{
        background: s.bg,
        border: `1.5px solid ${s.border}`,
        borderRadius: 10,
        padding: '10px 20px',
        minWidth: 140,
        textAlign: 'center',
      }}
    >
      <div style={{ color: s.label, fontSize: 13, fontWeight: 600 }}>
        {AGENT_LABELS[data.id] || data.label}
      </div>
      <div style={{
        color: s.text,
        fontSize: 11,
        marginTop: 3,
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
        fontWeight: 500,
      }}>
        {status === 'in_progress' ? 'working...' : status === 'waiting_approval' ? 'awaiting approval' : status}
      </div>
      {data.duration != null && status === 'done' && (
        <div style={{ color: '#9ca3af', fontSize: 10, marginTop: 2 }}>
          {data.duration.toFixed(1)}s
        </div>
      )}
    </motion.div>
  );
}

const nodeTypes = { agent: AgentNode };

const INITIAL_NODES = [
  { id: 'pm', type: 'agent', position: { x: 300, y: 0 }, data: { id: 'pm', status: 'queued', label: 'PM' } },
  { id: 'tech_lead', type: 'agent', position: { x: 300, y: 90 }, data: { id: 'tech_lead', status: 'queued', label: 'TL' } },
  { id: 'architect', type: 'agent', position: { x: 300, y: 180 }, data: { id: 'architect', status: 'queued', label: 'Arch' } },
  { id: 'backend_dev', type: 'agent', position: { x: 120, y: 280 }, data: { id: 'backend_dev', status: 'queued', label: 'BE' } },
  { id: 'frontend_dev', type: 'agent', position: { x: 480, y: 280 }, data: { id: 'frontend_dev', status: 'queued', label: 'FE' } },
  { id: 'qa', type: 'agent', position: { x: 300, y: 380 }, data: { id: 'qa', status: 'queued', label: 'QA' } },
  { id: 'deployer', type: 'agent', position: { x: 300, y: 470 }, data: { id: 'deployer', status: 'queued', label: 'Deploy' } },
];

const INITIAL_EDGES = [
  { id: 'pm-tl', source: 'pm', target: 'tech_lead', style: { stroke: '#d1d5db' } },
  { id: 'tl-arch', source: 'tech_lead', target: 'architect', style: { stroke: '#d1d5db' } },
  { id: 'arch-be', source: 'architect', target: 'backend_dev', style: { stroke: '#d1d5db' } },
  { id: 'arch-fe', source: 'architect', target: 'frontend_dev', style: { stroke: '#d1d5db' } },
  { id: 'be-qa', source: 'backend_dev', target: 'qa', style: { stroke: '#d1d5db' } },
  { id: 'fe-qa', source: 'frontend_dev', target: 'qa', style: { stroke: '#d1d5db' } },
  { id: 'qa-deployer', source: 'qa', target: 'deployer', style: { stroke: '#d1d5db' } },
];

export function PipelineDAG({ tasks }) {
  const nodes = useMemo(() => {
    return INITIAL_NODES.map((node) => {
      const task = tasks[node.id];
      const status = task?.status || 'queued';
      return {
        ...node,
        data: {
          ...node.data,
          status,
          duration: task?.completed_at && task?.started_at ? task.completed_at - task.started_at : null,
        },
      };
    });
  }, [tasks]);

  const edges = useMemo(() => {
    return INITIAL_EDGES.map((edge) => {
      const sourceTask = tasks[edge.source];
      const done = sourceTask?.status === 'done';
      return {
        ...edge,
        animated: !done && sourceTask?.status === 'in_progress',
        style: { stroke: done ? '#86efac' : '#d1d5db', strokeWidth: done ? 2 : 1 },
      };
    });
  }, [tasks]);

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.25 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag={false}
        zoomOnScroll={false}
        zoomOnPinch={false}
        zoomOnDoubleClick={false}
        preventScrolling={false}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#e5e7eb" gap={24} size={1} />
      </ReactFlow>
    </div>
  );
}

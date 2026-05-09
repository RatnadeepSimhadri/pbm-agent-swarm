import { useCallback, useMemo } from 'react';
import { ReactFlow, Background, useNodesState, useEdgesState } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { motion } from 'framer-motion';

const STATUS_COLORS = {
  queued: { bg: '#334155', border: '#475569', text: '#94a3b8' },
  assigned: { bg: '#1e3a5f', border: '#3b82f6', text: '#93c5fd' },
  in_progress: { bg: '#1e3a8a', border: '#3b82f6', text: '#bfdbfe' },
  done: { bg: '#14532d', border: '#22c55e', text: '#86efac' },
  failed: { bg: '#7f1d1d', border: '#ef4444', text: '#fca5a5' },
};

const AGENT_LABELS = {
  pm: 'Product Manager',
  tech_lead: 'Tech Lead',
  architect: 'Architect',
  backend_dev: 'Backend Dev',
  frontend_dev: 'Frontend Dev',
  qa: 'QA Engineer',
};

const AGENT_ICONS = {
  pm: '\u{1F4CB}',
  tech_lead: '\u{1F4CA}',
  architect: '\u{1F3D7}',
  backend_dev: '\u{2699}',
  frontend_dev: '\u{1F3A8}',
  qa: '\u{1F9EA}',
};

function AgentNode({ data }) {
  const status = data.status || 'queued';
  const colors = STATUS_COLORS[status];
  const isActive = status === 'in_progress';

  return (
    <motion.div
      animate={isActive ? {
        boxShadow: [
          `0 0 8px 2px ${colors.border}40`,
          `0 0 20px 6px ${colors.border}60`,
          `0 0 8px 2px ${colors.border}40`,
        ],
      } : { boxShadow: `0 0 0px 0px transparent` }}
      transition={isActive ? { duration: 2, repeat: Infinity } : {}}
      style={{
        background: colors.bg,
        border: `2px solid ${colors.border}`,
        borderRadius: 12,
        padding: '12px 18px',
        minWidth: 140,
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: 20, marginBottom: 4 }}>{AGENT_ICONS[data.id] || ''}</div>
      <div style={{ color: colors.text, fontSize: 13, fontWeight: 600 }}>
        {AGENT_LABELS[data.id] || data.label}
      </div>
      <div style={{
        color: colors.text,
        fontSize: 10,
        marginTop: 4,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        opacity: 0.8,
      }}>
        {status === 'in_progress' ? 'working...' : status}
      </div>
      {data.duration != null && status === 'done' && (
        <div style={{ color: colors.text, fontSize: 10, opacity: 0.6, marginTop: 2 }}>
          {data.duration.toFixed(1)}s
        </div>
      )}
    </motion.div>
  );
}

const nodeTypes = { agent: AgentNode };

const INITIAL_NODES = [
  { id: 'pm', type: 'agent', position: { x: 300, y: 0 }, data: { id: 'pm', status: 'queued', label: 'PM' } },
  { id: 'tech_lead', type: 'agent', position: { x: 300, y: 100 }, data: { id: 'tech_lead', status: 'queued', label: 'TL' } },
  { id: 'architect', type: 'agent', position: { x: 300, y: 200 }, data: { id: 'architect', status: 'queued', label: 'Arch' } },
  { id: 'backend_dev', type: 'agent', position: { x: 120, y: 310 }, data: { id: 'backend_dev', status: 'queued', label: 'BE' } },
  { id: 'frontend_dev', type: 'agent', position: { x: 480, y: 310 }, data: { id: 'frontend_dev', status: 'queued', label: 'FE' } },
  { id: 'qa', type: 'agent', position: { x: 300, y: 420 }, data: { id: 'qa', status: 'queued', label: 'QA' } },
];

const INITIAL_EDGES = [
  { id: 'pm-tl', source: 'pm', target: 'tech_lead', animated: true, style: { stroke: '#475569' } },
  { id: 'tl-arch', source: 'tech_lead', target: 'architect', animated: true, style: { stroke: '#475569' } },
  { id: 'arch-be', source: 'architect', target: 'backend_dev', animated: true, style: { stroke: '#475569' } },
  { id: 'arch-fe', source: 'architect', target: 'frontend_dev', animated: true, style: { stroke: '#475569' } },
  { id: 'be-qa', source: 'backend_dev', target: 'qa', animated: true, style: { stroke: '#475569' } },
  { id: 'fe-qa', source: 'frontend_dev', target: 'qa', animated: true, style: { stroke: '#475569' } },
];

export function PipelineDAG({ tasks }) {
  const nodes = useMemo(() => {
    return INITIAL_NODES.map((node) => {
      const task = tasks[node.id];
      const status = task?.status || 'queued';
      const colors = STATUS_COLORS[status];
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
        animated: !done,
        style: { stroke: done ? '#22c55e' : '#475569', strokeWidth: done ? 2 : 1 },
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
        fitViewOptions={{ padding: 0.3 }}
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
        <Background color="#1e293b" gap={20} size={1} />
      </ReactFlow>
    </div>
  );
}

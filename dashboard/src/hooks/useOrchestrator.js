import { useCallback, useEffect, useRef, useState } from 'react';

const WS_URL = 'ws://localhost:8001/ws';
const API_URL = 'http://localhost:8001';

const INITIAL_STATE = {
  connected: false,
  pipeline: null,
  tasks: {},
  agentOutputs: {},  // { agent_name: "accumulated text" }
  artifacts: [],
  metrics: { tasksCompleted: 0, tasksTotal: 0, tokensUsed: 0, elapsed: 0, linesGenerated: 0 },
  testResults: null,
};

export function useOrchestrator() {
  const [state, setState] = useState(INITIAL_STATE);
  const wsRef = useRef(null);
  const startTimeRef = useRef(null);
  const timerRef = useRef(null);

  // Process incoming WebSocket events
  const handleEvent = useCallback((event) => {
    setState((prev) => {
      const next = { ...prev };

      switch (event.type) {
        case 'pipeline_start': {
          const taskMap = {};
          event.data.tasks.forEach((t) => {
            taskMap[t.id] = t;
          });
          next.pipeline = { id: event.data.pipeline_id, intent: event.data.intent, status: 'running' };
          next.tasks = taskMap;
          next.agentOutputs = {};
          next.artifacts = [];
          next.metrics = { tasksCompleted: 0, tasksTotal: event.data.tasks.length, tokensUsed: 0, elapsed: 0, linesGenerated: 0 };
          next.testResults = null;
          break;
        }

        case 'pipeline_complete': {
          next.pipeline = { ...next.pipeline, status: event.data.status };
          next.metrics = {
            ...next.metrics,
            tasksCompleted: event.data.tasks_completed,
            tokensUsed: event.data.total_tokens,
            elapsed: event.data.elapsed,
          };
          break;
        }

        case 'task_state_change': {
          const { task_id, status, display_name, started_at, completed_at, error } = event.data;
          next.tasks = {
            ...next.tasks,
            [task_id]: { ...next.tasks[task_id], id: task_id, status, display_name, started_at, completed_at, error },
          };
          // Update completed count
          const completedCount = Object.values(next.tasks).filter((t) => t.status === 'done').length;
          next.metrics = { ...next.metrics, tasksCompleted: completedCount };
          break;
        }

        case 'agent_output': {
          const agent = event.agent;
          const content = event.data.content || '';
          next.agentOutputs = {
            ...next.agentOutputs,
            [agent]: (prev.agentOutputs[agent] || '') + content,
          };
          break;
        }

        case 'file_write': {
          const path = event.data.path;
          if (!prev.artifacts.includes(path)) {
            next.artifacts = [...prev.artifacts, path];
          }
          next.metrics = {
            ...next.metrics,
            linesGenerated: next.metrics.linesGenerated + (event.data.lines || 0),
          };
          break;
        }

        case 'tool_call': {
          // Append tool call info to agent output for visibility
          const toolAgent = event.agent;
          const toolInfo = `\n> Tool: ${event.data.tool}(${JSON.stringify(event.data.arguments).slice(0, 80)})\n`;
          next.agentOutputs = {
            ...next.agentOutputs,
            [toolAgent]: (prev.agentOutputs[toolAgent] || '') + toolInfo,
          };
          break;
        }

        case 'test_result': {
          next.testResults = event.data;
          break;
        }

        case 'metrics_update': {
          next.metrics = { ...next.metrics, ...event.data };
          break;
        }

        default:
          break;
      }

      return next;
    });
  }, []);

  // Connect WebSocket
  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setState((prev) => ({ ...prev, connected: true }));
    };

    ws.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data);
        handleEvent(event);
      } catch (e) {
        console.error('Failed to parse event:', e);
      }
    };

    ws.onclose = () => {
      setState((prev) => ({ ...prev, connected: false }));
    };

    ws.onerror = () => {
      setState((prev) => ({ ...prev, connected: false }));
    };

    return () => {
      ws.close();
    };
  }, [handleEvent]);

  // Elapsed time ticker
  useEffect(() => {
    if (state.pipeline?.status === 'running') {
      startTimeRef.current = Date.now() - (state.metrics.elapsed * 1000);
      timerRef.current = setInterval(() => {
        setState((prev) => ({
          ...prev,
          metrics: { ...prev.metrics, elapsed: (Date.now() - startTimeRef.current) / 1000 },
        }));
      }, 100);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [state.pipeline?.status]);

  // Start pipeline
  const startPipeline = useCallback(async (intent) => {
    const res = await fetch(`${API_URL}/api/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ intent }),
    });
    return res.json();
  }, []);

  // Fetch artifact content
  const fetchArtifact = useCallback(async (path) => {
    const res = await fetch(`${API_URL}/api/artifacts/${encodeURIComponent(path)}`);
    return res.json();
  }, []);

  return { ...state, startPipeline, fetchArtifact };
}

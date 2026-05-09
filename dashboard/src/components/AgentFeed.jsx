import { useEffect, useRef, useState } from 'react';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import javascript from 'react-syntax-highlighter/dist/esm/languages/hljs/javascript';
import json from 'react-syntax-highlighter/dist/esm/languages/hljs/json';
import { githubGist } from 'react-syntax-highlighter/dist/esm/styles/hljs';

SyntaxHighlighter.registerLanguage('python', python);
SyntaxHighlighter.registerLanguage('javascript', javascript);
SyntaxHighlighter.registerLanguage('jsx', javascript);
SyntaxHighlighter.registerLanguage('json', json);

const AGENTS = [
  { id: 'product_manager', label: 'PM' },
  { id: 'tech_lead', label: 'TL' },
  { id: 'architect', label: 'Arch' },
  { id: 'backend_dev', label: 'BE' },
  { id: 'frontend_dev', label: 'FE' },
  { id: 'qa_engineer', label: 'QA' },
];

const STATUS_DOT = {
  queued: 'bg-gray-300',
  assigned: 'bg-blue-300',
  in_progress: 'bg-blue-500 animate-pulse',
  done: 'bg-emerald-500',
  failed: 'bg-red-500',
};

export function AgentFeed({ agentOutputs, tasks }) {
  const [activeTab, setActiveTab] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    const activeAgent = Object.entries(tasks).find(([, t]) => t.status === 'in_progress');
    if (activeAgent) {
      const taskToAgent = {
        pm: 'product_manager',
        tech_lead: 'tech_lead',
        architect: 'architect',
        backend_dev: 'backend_dev',
        frontend_dev: 'frontend_dev',
        qa: 'qa_engineer',
      };
      setActiveTab(taskToAgent[activeAgent[0]] || activeAgent[0]);
    }
  }, [tasks]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [agentOutputs, activeTab]);

  const content = activeTab ? (agentOutputs[activeTab] || '') : '';

  const getAgentStatus = (agentId) => {
    const taskIdMap = {
      product_manager: 'pm',
      tech_lead: 'tech_lead',
      architect: 'architect',
      backend_dev: 'backend_dev',
      frontend_dev: 'frontend_dev',
      qa_engineer: 'qa',
    };
    const task = tasks[taskIdMap[agentId]];
    return task?.status || 'queued';
  };

  return (
    <div className="flex flex-col h-full">
      {/* Tabs */}
      <div className="flex border-b border-gray-200 bg-gray-50/50">
        {AGENTS.map(({ id, label }) => {
          const status = getAgentStatus(id);
          const isActive = activeTab === id;
          return (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium whitespace-nowrap transition-colors border-b-2 ${
                isActive
                  ? 'border-gray-900 text-gray-900'
                  : 'border-transparent text-gray-400 hover:text-gray-600'
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[status]}`} />
              {label}
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 font-mono text-xs leading-relaxed">
        {content ? (
          <RenderOutput text={content} />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm font-sans">
            {activeTab ? 'Waiting for agent output...' : 'Select an agent tab above'}
          </div>
        )}
      </div>
    </div>
  );
}

function RenderOutput({ text }) {
  const parts = [];
  const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;

  while ((match = codeBlockRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: text.slice(lastIndex, match.index) });
    }
    parts.push({ type: 'code', language: match[1] || 'python', content: match[2] });
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    parts.push({ type: 'text', content: text.slice(lastIndex) });
  }

  return (
    <div className="space-y-2">
      {parts.map((part, i) => {
        if (part.type === 'code') {
          return (
            <SyntaxHighlighter
              key={i}
              language={part.language}
              style={githubGist}
              customStyle={{
                background: '#f9fafb',
                borderRadius: 8,
                padding: 14,
                fontSize: 11,
                border: '1px solid #e5e7eb',
              }}
              wrapLongLines
            >
              {part.content.trim()}
            </SyntaxHighlighter>
          );
        }
        return (
          <div key={i} className="text-gray-600 whitespace-pre-wrap">
            {part.content.split('\n').map((line, j) => {
              if (line.startsWith('> Tool:')) {
                return (
                  <div key={j} className="text-amber-700 bg-amber-50 border border-amber-100 px-2.5 py-1 rounded my-1 text-[11px]">
                    {line}
                  </div>
                );
              }
              return <span key={j}>{line}{'\n'}</span>;
            })}
          </div>
        );
      })}
    </div>
  );
}

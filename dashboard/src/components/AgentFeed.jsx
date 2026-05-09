import { useEffect, useRef, useState } from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import javascript from 'react-syntax-highlighter/dist/esm/languages/hljs/javascript';
import json from 'react-syntax-highlighter/dist/esm/languages/hljs/json';
import { githubGist } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import { MermaidDiagram } from './MermaidDiagram';
import { DeployApproval } from './DeployApproval';

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
  { id: 'deployer', label: 'Deploy' },
];

const STATUS_DOT = {
  queued: 'bg-gray-300',
  assigned: 'bg-blue-300',
  in_progress: 'bg-blue-500 animate-pulse',
  waiting_approval: 'bg-amber-500 animate-pulse',
  done: 'bg-emerald-500',
  failed: 'bg-red-500',
};

const TASK_TO_AGENT = {
  pm: 'product_manager',
  tech_lead: 'tech_lead',
  architect: 'architect',
  backend_dev: 'backend_dev',
  frontend_dev: 'frontend_dev',
  qa: 'qa_engineer',
  deployer: 'deployer',
};

const AGENT_TO_TASK = {
  product_manager: 'pm',
  tech_lead: 'tech_lead',
  architect: 'architect',
  backend_dev: 'backend_dev',
  frontend_dev: 'frontend_dev',
  qa_engineer: 'qa',
  deployer: 'deployer',
};

export function AgentFeed({ agentOutputs, tasks, deployFiles, deployPending, deployResult, onApprove, onReject, fetchArtifact }) {
  const [activeTab, setActiveTab] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    // Auto-switch to waiting_approval (deployer) or in_progress agent
    const waitingAgent = Object.entries(tasks).find(([, t]) => t.status === 'waiting_approval');
    if (waitingAgent) {
      const taskToAgent = TASK_TO_AGENT;
      setActiveTab(taskToAgent[waitingAgent[0]] || waitingAgent[0]);
      return;
    }
    const activeAgent = Object.entries(tasks).find(([, t]) => t.status === 'in_progress');
    if (activeAgent) {
      const taskToAgent = TASK_TO_AGENT;
      setActiveTab(taskToAgent[activeAgent[0]] || activeAgent[0]);
    }
  }, [tasks]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [agentOutputs, activeTab]);

  const content = activeTab ? (agentOutputs[activeTab] || '') : '';
  const isDeployerTab = activeTab === 'deployer';
  const showDeployUI = isDeployerTab && (deployPending || deployResult);

  const getAgentStatus = (agentId) => {
    const task = tasks[AGENT_TO_TASK[agentId]];
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
      {showDeployUI ? (
        <div className="flex-1 overflow-hidden">
          <DeployApproval
            files={deployFiles}
            pending={deployPending}
            result={deployResult}
            onApprove={onApprove}
            onReject={onReject}
            fetchArtifact={fetchArtifact}
          />
        </div>
      ) : (
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 text-xs leading-relaxed">
          {content ? (
            <RenderOutput text={content} />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400 text-sm">
              {activeTab ? 'Waiting for agent output...' : 'Select an agent tab above'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function RenderOutput({ text }) {
  // Split text into tool-call lines and markdown sections
  const parts = [];
  const lines = text.split('\n');
  let mdBuffer = [];

  const flushMd = () => {
    if (mdBuffer.length > 0) {
      parts.push({ type: 'md', content: mdBuffer.join('\n') });
      mdBuffer = [];
    }
  };

  for (const line of lines) {
    if (line.startsWith('> Tool:')) {
      flushMd();
      parts.push({ type: 'tool', content: line });
    } else {
      mdBuffer.push(line);
    }
  }
  flushMd();

  return (
    <div className="space-y-1">
      {parts.map((part, i) => {
        if (part.type === 'tool') {
          return (
            <div key={i} className="text-amber-700 bg-amber-50 border border-amber-100 px-2.5 py-1 rounded text-[11px] font-mono">
              {part.content}
            </div>
          );
        }
        return (
          <div key={i}>
            <Markdown remarkPlugins={[remarkGfm]} components={agentMarkdownComponents}>{part.content}</Markdown>
          </div>
        );
      })}
    </div>
  );
}

const agentMarkdownComponents = {
  h1({ children }) {
    return (
      <div className="mb-3">
        <h1 className="text-sm font-semibold text-gray-900 leading-snug">{children}</h1>
        <div className="mt-1 h-px bg-gradient-to-r from-gray-200 to-transparent" />
      </div>
    );
  },

  h2({ children }) {
    return (
      <div className="mt-4 mb-1.5">
        <h2 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400">{children}</h2>
      </div>
    );
  },

  h3({ children }) {
    return <h3 className="text-[12px] font-semibold text-gray-800 mt-3 mb-1">{children}</h3>;
  },

  p({ children }) {
    return <p className="text-[12px] text-gray-600 leading-relaxed mb-2 text-justify">{children}</p>;
  },

  ul({ children }) {
    return <ul className="space-y-1 my-1.5 list-none pl-0">{children}</ul>;
  },

  ol({ children }) {
    return <ol className="space-y-1 my-1.5 list-none pl-0">{children}</ol>;
  },

  li({ children }) {
    return (
      <li className="flex gap-2 text-[12px] text-gray-600 leading-relaxed">
        <span className="text-gray-300 mt-0.5 shrink-0">&#x2022;</span>
        <span>{children}</span>
      </li>
    );
  },

  strong({ children }) {
    return <strong className="font-semibold text-gray-800">{children}</strong>;
  },

  em({ children }) {
    return <em className="italic text-gray-500">{children}</em>;
  },

  blockquote({ children }) {
    return (
      <blockquote className="border-l-2 border-gray-200 pl-3 my-2 text-[12px] text-gray-500 italic">
        {children}
      </blockquote>
    );
  },

  table({ children }) {
    return (
      <div className="my-2 overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-[11px]">{children}</table>
      </div>
    );
  },

  thead({ children }) {
    return <thead className="bg-gray-50">{children}</thead>;
  },

  th({ children }) {
    return <th className="text-left px-3 py-1.5 font-medium text-gray-700 border-b border-gray-200">{children}</th>;
  },

  td({ children }) {
    return <td className="px-3 py-1.5 text-gray-600 border-b border-gray-100">{children}</td>;
  },

  code({ className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || '');
    if (match) {
      if (match[1] === 'mermaid') {
        return <MermaidDiagram chart={String(children)} />;
      }
      return (
        <SyntaxHighlighter
          language={match[1]}
          style={githubGist}
          customStyle={{
            background: '#f9fafb',
            borderRadius: 8,
            padding: 12,
            fontSize: 11,
            border: '1px solid #e5e7eb',
            margin: '8px 0',
          }}
          wrapLongLines
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      );
    }
    return (
      <code className="text-[11px] font-medium text-gray-800 bg-gray-100 px-1 py-0.5 rounded" {...props}>
        {children}
      </code>
    );
  },

  pre({ children }) {
    return <>{children}</>;
  },

  hr() {
    return <div className="my-3 h-px bg-gray-100" />;
  },
};

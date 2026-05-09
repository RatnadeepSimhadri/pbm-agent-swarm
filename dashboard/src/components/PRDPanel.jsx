import { useEffect, useRef } from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function PRDPanel({ content }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [content]);

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
        <h3 className="text-sm font-medium text-gray-900">Product Requirements</h3>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4">
        {content ? (
          <Markdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{content}</Markdown>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            Waiting for Product Manager agent...
          </div>
        )}
      </div>
    </div>
  );
}

const markdownComponents = {
  h1({ children }) {
    return (
      <div className="mb-4">
        <h1 className="text-base font-semibold text-gray-900 leading-snug">{children}</h1>
        <div className="mt-1.5 h-px bg-gradient-to-r from-gray-200 to-transparent" />
      </div>
    );
  },

  h2({ children }) {
    return (
      <div className="mt-5 mb-2">
        <h2 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400">{children}</h2>
      </div>
    );
  },

  h3({ children }) {
    return (
      <h3 className="text-[13px] font-semibold text-gray-800 mt-3 mb-1">{children}</h3>
    );
  },

  p({ children }) {
    return (
      <p className="text-[13px] text-gray-600 leading-relaxed mb-2.5 text-justify">{children}</p>
    );
  },

  ul({ children }) {
    return <ul className="space-y-1.5 my-2 list-none pl-0">{children}</ul>;
  },

  ol({ children }) {
    return <ol className="space-y-1.5 my-2 list-none pl-0 counter-reset-[item]">{children}</ol>;
  },

  li({ children, ordered }) {
    return (
      <li className="flex gap-2 text-[13px] text-gray-600 leading-relaxed">
        <span className="text-gray-300 mt-0.5 shrink-0">&#x2022;</span>
        <span className="text-justify">{children}</span>
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
      <blockquote className="border-l-2 border-gray-200 pl-3 my-3 text-[13px] text-gray-500 italic">
        {children}
      </blockquote>
    );
  },

  code({ className, children }) {
    if (className) {
      return (
        <pre className="bg-gray-50 border border-gray-200 rounded-lg p-3 my-2 overflow-x-auto">
          <code className="text-[11px] text-gray-700 font-mono">{children}</code>
        </pre>
      );
    }
    return (
      <code className="text-[12px] font-medium text-gray-800 bg-gray-100 px-1.5 py-0.5 rounded">
        {children}
      </code>
    );
  },

  hr() {
    return <div className="my-4 h-px bg-gray-100" />;
  },
};

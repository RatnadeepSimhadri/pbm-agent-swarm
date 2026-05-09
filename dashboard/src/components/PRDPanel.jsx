import { useEffect, useRef } from 'react';
import Markdown from 'react-markdown';

export function PRDPanel({ content }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [content]);

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-surface-lighter flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-accent-500" />
        <h3 className="text-sm font-semibold text-slate-200">Product Requirements</h3>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4">
        {content ? (
          <div className="prose prose-sm prose-invert max-w-none
            prose-headings:text-slate-200 prose-headings:font-semibold
            prose-h1:text-lg prose-h2:text-base prose-h3:text-sm
            prose-p:text-slate-400 prose-p:leading-relaxed prose-p:text-sm
            prose-li:text-slate-400 prose-li:text-sm
            prose-strong:text-slate-300
            prose-blockquote:border-accent-600 prose-blockquote:text-slate-400
            prose-code:text-accent-400 prose-code:bg-surface-lighter prose-code:px-1 prose-code:rounded
          ">
            <Markdown>{content}</Markdown>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-slate-500 text-sm">
            Waiting for Product Manager agent...
          </div>
        )}
      </div>
    </div>
  );
}

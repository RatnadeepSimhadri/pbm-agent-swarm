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
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
        <h3 className="text-sm font-medium text-gray-900">Product Requirements</h3>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-5">
        {content ? (
          <div className="prose prose-sm max-w-none
            prose-headings:text-gray-900 prose-headings:font-semibold
            prose-h1:text-lg prose-h2:text-base prose-h3:text-sm
            prose-p:text-gray-600 prose-p:leading-relaxed prose-p:text-sm
            prose-li:text-gray-600 prose-li:text-sm
            prose-strong:text-gray-800
            prose-blockquote:border-gray-300 prose-blockquote:text-gray-500
            prose-code:text-gray-800 prose-code:bg-gray-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:font-medium
          ">
            <Markdown>{content}</Markdown>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            Waiting for Product Manager agent...
          </div>
        )}
      </div>
    </div>
  );
}

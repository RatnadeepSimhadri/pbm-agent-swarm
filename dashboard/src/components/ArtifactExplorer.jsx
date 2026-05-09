import { useState } from 'react';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import javascript from 'react-syntax-highlighter/dist/esm/languages/hljs/javascript';
import markdown from 'react-syntax-highlighter/dist/esm/languages/hljs/markdown';
import { githubGist } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import { motion, AnimatePresence } from 'framer-motion';

SyntaxHighlighter.registerLanguage('python', python);
SyntaxHighlighter.registerLanguage('javascript', javascript);
SyntaxHighlighter.registerLanguage('jsx', javascript);
SyntaxHighlighter.registerLanguage('markdown', markdown);

function getFileIcon(path) {
  if (path.endsWith('.py')) return 'py';
  if (path.endsWith('.jsx') || path.endsWith('.js')) return 'js';
  if (path.endsWith('.md')) return 'md';
  return 'f';
}

function getIconColor(path) {
  if (path.endsWith('.py')) return 'text-blue-600 bg-blue-50';
  if (path.endsWith('.jsx') || path.endsWith('.js')) return 'text-amber-600 bg-amber-50';
  if (path.endsWith('.md')) return 'text-gray-600 bg-gray-100';
  return 'text-gray-500 bg-gray-50';
}

function getLanguage(path) {
  if (path.endsWith('.py')) return 'python';
  if (path.endsWith('.jsx') || path.endsWith('.js')) return 'javascript';
  if (path.endsWith('.md')) return 'markdown';
  if (path.endsWith('.json')) return 'json';
  return 'text';
}

export function ArtifactExplorer({ artifacts, fetchArtifact }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [loading, setLoading] = useState(false);

  const handleClick = async (path) => {
    if (selectedFile === path) {
      setSelectedFile(null);
      return;
    }
    setSelectedFile(path);
    setLoading(true);
    try {
      const data = await fetchArtifact(path);
      setFileContent(data.content || '');
    } catch {
      setFileContent('Failed to load file.');
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-amber-500" />
          <h3 className="text-sm font-medium text-gray-900">Artifacts</h3>
        </div>
        <span className="text-xs text-gray-400">{artifacts.length} files</span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {artifacts.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            No files yet...
          </div>
        ) : (
          <div className="py-1">
            {artifacts.map((path) => (
              <div key={path}>
                <button
                  onClick={() => handleClick(path)}
                  className={`w-full text-left px-4 py-2.5 text-xs flex items-center gap-2.5 transition-colors ${
                    selectedFile === path
                      ? 'bg-gray-100 text-gray-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', duration: 0.3 }}
                    className={`w-5 h-5 rounded flex items-center justify-center text-[9px] font-bold ${getIconColor(path)}`}
                  >
                    {getFileIcon(path)}
                  </motion.span>
                  <span className="truncate font-mono">{path}</span>
                </button>

                <AnimatePresence>
                  {selectedFile === path && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden border-y border-gray-100"
                    >
                      {loading ? (
                        <div className="p-4 text-xs text-gray-400">Loading...</div>
                      ) : (
                        <SyntaxHighlighter
                          language={getLanguage(path)}
                          style={githubGist}
                          customStyle={{
                            background: '#f9fafb',
                            padding: 12,
                            fontSize: 10,
                            margin: 0,
                            maxHeight: 300,
                          }}
                          showLineNumbers
                          lineNumberStyle={{ color: '#d1d5db', fontSize: 9 }}
                          wrapLongLines
                        >
                          {fileContent}
                        </SyntaxHighlighter>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

import { useState } from 'react';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import javascript from 'react-syntax-highlighter/dist/esm/languages/hljs/javascript';
import markdown from 'react-syntax-highlighter/dist/esm/languages/hljs/markdown';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import { motion, AnimatePresence } from 'framer-motion';

SyntaxHighlighter.registerLanguage('python', python);
SyntaxHighlighter.registerLanguage('javascript', javascript);
SyntaxHighlighter.registerLanguage('jsx', javascript);
SyntaxHighlighter.registerLanguage('markdown', markdown);

const FILE_ICONS = {
  '.py': '\u{1F40D}',
  '.jsx': '\u{269B}',
  '.md': '\u{1F4DD}',
  '.json': '\u{1F4E6}',
};

function getFileIcon(path) {
  const ext = path.slice(path.lastIndexOf('.'));
  return FILE_ICONS[ext] || '\u{1F4C4}';
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
      <div className="px-4 py-3 border-b border-surface-lighter flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-amber-500" />
          <h3 className="text-sm font-semibold text-slate-200">Artifacts</h3>
        </div>
        <span className="text-xs text-slate-500">{artifacts.length} files</span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {artifacts.length === 0 ? (
          <div className="flex items-center justify-center h-full text-slate-500 text-sm">
            No files yet...
          </div>
        ) : (
          <div className="py-1">
            {artifacts.map((path) => (
              <div key={path}>
                <button
                  onClick={() => handleClick(path)}
                  className={`w-full text-left px-4 py-2 text-xs flex items-center gap-2 transition-colors ${
                    selectedFile === path
                      ? 'bg-surface-lighter text-slate-200'
                      : 'text-slate-400 hover:bg-surface-light hover:text-slate-300'
                  }`}
                >
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', duration: 0.3 }}
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
                      className="overflow-hidden border-y border-surface-lighter"
                    >
                      {loading ? (
                        <div className="p-4 text-xs text-slate-500">Loading...</div>
                      ) : (
                        <SyntaxHighlighter
                          language={getLanguage(path)}
                          style={atomOneDark}
                          customStyle={{
                            background: '#0c1222',
                            padding: 12,
                            fontSize: 10,
                            margin: 0,
                            maxHeight: 300,
                          }}
                          showLineNumbers
                          lineNumberStyle={{ color: '#334155', fontSize: 9 }}
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

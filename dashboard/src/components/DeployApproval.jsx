import { useState } from 'react';

const FILE_ICONS = {
  py: '🐍',
  jsx: '⚛️',
  js: '📜',
  css: '🎨',
  md: '📝',
};

function getFileIcon(path) {
  const ext = path.split('.').pop();
  return FILE_ICONS[ext] || '📄';
}

function FileRow({ file, onPreview }) {
  return (
    <button
      onClick={() => onPreview(file.path)}
      className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors text-left group"
    >
      <span className="text-sm">{getFileIcon(file.path)}</span>
      <span className="flex-1 text-sm font-mono text-slate-700 truncate group-hover:text-primary-700">
        {file.path}
      </span>
      <span className="text-xs text-slate-400">{file.lines} lines</span>
    </button>
  );
}

export function DeployApproval({ files, pending, result, onApprove, onReject, fetchArtifact }) {
  const [previewPath, setPreviewPath] = useState(null);
  const [previewContent, setPreviewContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [acting, setActing] = useState(false);

  const handlePreview = async (path) => {
    if (previewPath === path) {
      setPreviewPath(null);
      return;
    }
    setPreviewPath(path);
    setPreviewContent('Loading...');
    try {
      const data = await fetchArtifact(path);
      setPreviewContent(data.content || 'Empty file');
    } catch {
      setPreviewContent('Failed to load file');
    }
  };

  const handleApprove = async () => {
    setActing(true);
    await onApprove();
  };

  const handleReject = async () => {
    setActing(true);
    await onReject();
  };

  const totalLines = files.reduce((sum, f) => sum + f.lines, 0);

  // Post-action state
  if (result) {
    const deployed = result.status === 'deployed';
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="text-center space-y-3">
          <div className="text-4xl">{deployed ? '✅' : '⛔'}</div>
          <h3 className="text-lg font-semibold text-slate-900">
            {deployed ? 'Deployed Successfully' : 'Deployment Rejected'}
          </h3>
          <p className="text-sm text-slate-500">
            {deployed
              ? `${result.files_deployed} files applied to seed-app`
              : 'No files were modified'}
          </p>
          {deployed && (
            <p className="text-xs text-slate-400 mt-4">
              Run <code className="bg-gray-100 px-1.5 py-0.5 rounded">make dev</code> to see the changes.
              Use <code className="bg-gray-100 px-1.5 py-0.5 rounded">make revert</code> to undo.
            </p>
          )}
        </div>
      </div>
    );
  }

  // Waiting / acting state
  if (acting) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="text-center space-y-3">
          <div className="animate-spin text-3xl">⚙️</div>
          <p className="text-sm text-slate-500">Deploying files to seed-app...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-200">
        <h3 className="text-base font-semibold text-slate-900">Review & Deploy</h3>
        <p className="text-xs text-slate-500 mt-0.5">
          {files.length} files, {totalLines} total lines ready to apply to seed-app
        </p>
      </div>

      {/* File list */}
      <div className="flex-1 overflow-y-auto px-3 py-2">
        {files.map((file) => (
          <div key={file.path}>
            <FileRow file={file} onPreview={handlePreview} />
            {previewPath === file.path && (
              <div className="mx-3 mb-2 rounded-lg border border-gray-200 bg-gray-50 overflow-hidden">
                <pre className="p-3 text-xs font-mono text-slate-700 overflow-x-auto max-h-60">
                  {previewContent}
                </pre>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Action buttons */}
      <div className="px-5 py-4 border-t border-gray-200 flex gap-3">
        <button
          onClick={handleApprove}
          disabled={!pending}
          className="flex-1 px-4 py-2.5 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
        >
          Approve & Deploy
        </button>
        <button
          onClick={handleReject}
          disabled={!pending}
          className="px-4 py-2.5 border border-red-300 text-red-600 rounded-lg text-sm font-medium hover:bg-red-50 disabled:opacity-50 transition-colors"
        >
          Reject
        </button>
      </div>
    </div>
  );
}

import { motion } from 'framer-motion';

function formatTime(seconds) {
  if (seconds == null || seconds === 0) return '0.0s';
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s.toFixed(0)}s`;
}

function formatNumber(n) {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

export function MetricsBar({ metrics, testResults, pipeline }) {
  const isRunning = pipeline?.status === 'running';
  const isComplete = pipeline?.status === 'completed';
  const isFailed = pipeline?.status === 'failed';

  return (
    <div className="flex items-center gap-6 px-6 py-3 bg-white border-t border-gray-200">
      {/* Pipeline status */}
      <div className="flex items-center gap-2">
        {isRunning && (
          <motion.div
            className="w-2 h-2 rounded-full bg-blue-500"
            animate={{ opacity: [1, 0.3, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
        )}
        {isComplete && <div className="w-2 h-2 rounded-full bg-emerald-500" />}
        {isFailed && <div className="w-2 h-2 rounded-full bg-red-500" />}
        {!pipeline && <div className="w-2 h-2 rounded-full bg-gray-300" />}
        <span className="text-xs font-medium text-gray-500">
          {isRunning ? 'Running' : isComplete ? 'Complete' : isFailed ? 'Failed' : 'Idle'}
        </span>
      </div>

      <div className="h-4 w-px bg-gray-200" />

      <Metric label="Tasks" value={`${metrics.tasksCompleted}/${metrics.tasksTotal}`} />
      <Metric label="Time" value={formatTime(metrics.elapsed)} />
      <Metric label="Tokens" value={formatNumber(metrics.tokensUsed)} />
      <Metric label="Lines" value={formatNumber(metrics.linesGenerated)} />

      {testResults && (
        <>
          <div className="h-4 w-px bg-gray-200" />
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-gray-400">Tests:</span>
            <span className="text-xs font-mono text-emerald-600">{testResults.passed} passed</span>
            {testResults.failed > 0 && (
              <span className="text-xs font-mono text-red-600">{testResults.failed} failed</span>
            )}
          </div>
        </>
      )}

      <div className="flex-1" />
      {pipeline && (
        <div className="w-32 h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <motion.div
            className={`h-full rounded-full ${isComplete ? 'bg-emerald-500' : isFailed ? 'bg-red-500' : 'bg-gray-900'}`}
            initial={{ width: 0 }}
            animate={{ width: `${(metrics.tasksCompleted / Math.max(metrics.tasksTotal, 1)) * 100}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
      )}
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-xs text-gray-400">{label}</span>
      <span className="text-xs font-mono font-medium text-gray-700">{value}</span>
    </div>
  );
}

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
    <div className="flex items-center gap-6 px-6 py-3 bg-surface border-t border-surface-lighter">
      {/* Pipeline status */}
      <div className="flex items-center gap-2">
        {isRunning && (
          <motion.div
            className="w-2 h-2 rounded-full bg-blue-500"
            animate={{ opacity: [1, 0.3, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
        )}
        {isComplete && <div className="w-2 h-2 rounded-full bg-green-500" />}
        {isFailed && <div className="w-2 h-2 rounded-full bg-red-500" />}
        {!pipeline && <div className="w-2 h-2 rounded-full bg-slate-600" />}
        <span className="text-xs font-medium text-slate-400">
          {isRunning ? 'Running' : isComplete ? 'Complete' : isFailed ? 'Failed' : 'Idle'}
        </span>
      </div>

      <div className="h-4 w-px bg-surface-lighter" />

      {/* Tasks */}
      <Metric label="Tasks" value={`${metrics.tasksCompleted}/${metrics.tasksTotal}`} />

      {/* Elapsed */}
      <Metric label="Time" value={formatTime(metrics.elapsed)} />

      {/* Tokens */}
      <Metric label="Tokens" value={formatNumber(metrics.tokensUsed)} />

      {/* Lines */}
      <Metric label="Lines" value={formatNumber(metrics.linesGenerated)} />

      {/* Test results */}
      {testResults && (
        <>
          <div className="h-4 w-px bg-surface-lighter" />
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-500">Tests:</span>
            <span className="text-xs font-mono text-green-400">{testResults.passed} passed</span>
            {testResults.failed > 0 && (
              <span className="text-xs font-mono text-red-400">{testResults.failed} failed</span>
            )}
          </div>
        </>
      )}

      {/* Spacer + progress bar */}
      <div className="flex-1" />
      {pipeline && (
        <div className="w-32 h-1.5 bg-surface-lighter rounded-full overflow-hidden">
          <motion.div
            className={`h-full rounded-full ${isComplete ? 'bg-green-500' : isFailed ? 'bg-red-500' : 'bg-primary-500'}`}
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
      <span className="text-xs text-slate-500">{label}</span>
      <span className="text-xs font-mono font-medium text-slate-300">{value}</span>
    </div>
  );
}

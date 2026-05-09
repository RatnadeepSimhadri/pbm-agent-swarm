import { useState } from 'react';
import { motion } from 'framer-motion';

const DEFAULT_INTENT = 'Members should be able to check what their medications will cost before filling them';

export function IntentInput({ onSubmit, isRunning, connected }) {
  const [intent, setIntent] = useState(DEFAULT_INTENT);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (intent.trim() && !isRunning) {
      onSubmit(intent.trim());
    }
  };

  return (
    <div className="px-6 py-4 bg-surface border-b border-surface-lighter">
      <form onSubmit={handleSubmit} className="flex items-center gap-4">
        {/* Logo */}
        <div className="flex items-center gap-3 mr-2">
          <div className="w-8 h-8 bg-primary-800 rounded-lg flex items-center justify-center">
            <span className="text-lg">{'\u{1F916}'}</span>
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-200 leading-tight">Agent Swarm</h1>
            <p className="text-[10px] text-slate-500">PBM Dev Pipeline</p>
          </div>
        </div>

        <div className="h-8 w-px bg-surface-lighter" />

        {/* Input */}
        <div className="flex-1 relative">
          <input
            type="text"
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
            placeholder="Describe a feature to build..."
            disabled={isRunning}
            className="w-full px-4 py-2.5 bg-surface-light border border-surface-lighter rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-primary-600 disabled:opacity-50 transition-all"
          />
        </div>

        {/* Submit */}
        <motion.button
          type="submit"
          disabled={isRunning || !connected || !intent.trim()}
          whileHover={!isRunning ? { scale: 1.02 } : {}}
          whileTap={!isRunning ? { scale: 0.98 } : {}}
          className="px-6 py-2.5 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-lg disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {isRunning ? (
            <>
              <motion.span
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="inline-block"
              >
                {'\u{2699}'}
              </motion.span>
              Running...
            </>
          ) : (
            <>
              <span>{'\u{25B6}'}</span>
              Build Feature
            </>
          )}
        </motion.button>

        {/* Connection indicator */}
        <div className="flex items-center gap-1.5" title={connected ? 'Connected' : 'Disconnected'}>
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-[10px] text-slate-500">{connected ? 'WS' : 'OFF'}</span>
        </div>
      </form>
    </div>
  );
}

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
    <div className="px-6 py-4 bg-white border-b border-gray-200">
      <form onSubmit={handleSubmit} className="flex items-center gap-4">
        {/* Logo */}
        <div className="flex items-center gap-3 mr-2">
          <div className="w-8 h-8 bg-gray-900 rounded-lg flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-gray-900 leading-tight">Agent Swarm</h1>
            <p className="text-[10px] text-gray-400">PBM Dev Pipeline</p>
          </div>
        </div>

        <div className="h-8 w-px bg-gray-200" />

        {/* Input */}
        <div className="flex-1 relative">
          <input
            type="text"
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
            placeholder="Describe a feature to build..."
            disabled={isRunning}
            className="w-full px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent disabled:opacity-50 transition-all"
          />
        </div>

        {/* Submit */}
        <motion.button
          type="submit"
          disabled={isRunning || !connected || !intent.trim()}
          whileHover={!isRunning ? { scale: 1.01 } : {}}
          whileTap={!isRunning ? { scale: 0.99 } : {}}
          className="px-5 py-2 bg-gray-900 hover:bg-gray-800 text-white text-sm font-medium rounded-lg disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {isRunning ? (
            <>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full"
              />
              Running...
            </>
          ) : (
            'Build Feature'
          )}
        </motion.button>

        {/* Connection indicator */}
        <div className="flex items-center gap-1.5" title={connected ? 'Connected' : 'Disconnected'}>
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-500' : 'bg-red-500'}`} />
        </div>
      </form>
    </div>
  );
}

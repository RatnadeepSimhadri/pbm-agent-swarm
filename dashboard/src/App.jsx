import { useOrchestrator } from './hooks/useOrchestrator';
import { IntentInput } from './components/IntentInput';
import { PipelineDAG } from './components/PipelineDAG';
import { PRDPanel } from './components/PRDPanel';
import { AgentFeed } from './components/AgentFeed';
import { ArtifactExplorer } from './components/ArtifactExplorer';
import { MetricsBar } from './components/MetricsBar';

export default function App() {
  const {
    connected,
    pipeline,
    tasks,
    agentOutputs,
    artifacts,
    metrics,
    testResults,
    startPipeline,
    fetchArtifact,
  } = useOrchestrator();

  const prdContent = agentOutputs['product_manager'] || '';
  const isRunning = pipeline?.status === 'running';

  return (
    <div className="h-screen flex flex-col bg-surface overflow-hidden">
      {/* Top bar — intent input */}
      <IntentInput
        onSubmit={startPipeline}
        isRunning={isRunning}
        connected={connected}
      />

      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: PRD Panel (25%) */}
        <div className="w-1/4 border-r border-surface-lighter overflow-hidden">
          <PRDPanel content={prdContent} />
        </div>

        {/* Center: DAG + Agent Feed (50%) */}
        <div className="w-1/2 flex flex-col border-r border-surface-lighter">
          {/* DAG visualization */}
          <div className="h-[280px] border-b border-surface-lighter">
            <PipelineDAG tasks={tasks} />
          </div>

          {/* Agent Feed */}
          <div className="flex-1 overflow-hidden">
            <AgentFeed agentOutputs={agentOutputs} tasks={tasks} />
          </div>
        </div>

        {/* Right: Artifact Explorer (25%) */}
        <div className="w-1/4 overflow-hidden">
          <ArtifactExplorer artifacts={artifacts} fetchArtifact={fetchArtifact} />
        </div>
      </div>

      {/* Bottom bar — metrics */}
      <MetricsBar
        metrics={metrics}
        testResults={testResults}
        pipeline={pipeline}
      />
    </div>
  );
}

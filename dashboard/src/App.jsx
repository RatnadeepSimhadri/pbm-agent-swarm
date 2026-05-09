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
    deployFiles,
    deployPending,
    deployResult,
    startPipeline,
    fetchArtifact,
    approveDeploy,
    rejectDeploy,
  } = useOrchestrator();

  const prdContent = agentOutputs['product_manager'] || '';
  const isRunning = pipeline?.status === 'running';

  return (
    <div className="h-screen flex flex-col bg-gray-50 overflow-hidden">
      {/* Top bar */}
      <IntentInput
        onSubmit={startPipeline}
        isRunning={isRunning}
        connected={connected}
      />

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: PRD Panel */}
        <div className="w-1/4 border-r border-gray-200 bg-white overflow-hidden">
          <PRDPanel content={prdContent} />
        </div>

        {/* Center: DAG + Agent Feed */}
        <div className="w-1/2 flex flex-col">
          <div className="h-[340px] border-b border-gray-200 bg-gray-50/50">
            <PipelineDAG tasks={tasks} />
          </div>
          <div className="flex-1 overflow-hidden bg-white border-r border-gray-200">
            <AgentFeed
              agentOutputs={agentOutputs}
              tasks={tasks}
              deployFiles={deployFiles}
              deployPending={deployPending}
              deployResult={deployResult}
              onApprove={approveDeploy}
              onReject={rejectDeploy}
              fetchArtifact={fetchArtifact}
            />
          </div>
        </div>

        {/* Right: Artifact Explorer */}
        <div className="w-1/4 bg-white overflow-hidden">
          <ArtifactExplorer artifacts={artifacts} fetchArtifact={fetchArtifact} />
        </div>
      </div>

      {/* Bottom bar */}
      <MetricsBar
        metrics={metrics}
        testResults={testResults}
        pipeline={pipeline}
      />
    </div>
  );
}

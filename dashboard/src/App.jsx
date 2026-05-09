import { useCallback, useRef, useState } from 'react';
import { useOrchestrator } from './hooks/useOrchestrator';
import { IntentInput } from './components/IntentInput';
import { PipelineDAG } from './components/PipelineDAG';
import { PRDPanel } from './components/PRDPanel';
import { AgentFeed } from './components/AgentFeed';
import { ArtifactExplorer } from './components/ArtifactExplorer';
import { MetricsBar } from './components/MetricsBar';

function ResizeHandle({ onDrag }) {
  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    const onMouseMove = (e) => onDrag(e.clientX);
    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, [onDrag]);

  return (
    <div
      onMouseDown={handleMouseDown}
      className="w-1 cursor-col-resize hover:bg-primary-300 active:bg-primary-400 transition-colors bg-gray-200 flex-shrink-0"
    />
  );
}

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

  const containerRef = useRef(null);
  const [leftWidth, setLeftWidth] = useState(25);   // % of container
  const [rightWidth, setRightWidth] = useState(25);  // % of container

  const handleLeftDrag = useCallback((clientX) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const pct = ((clientX - rect.left) / rect.width) * 100;
    setLeftWidth(Math.max(15, Math.min(45, pct)));
  }, []);

  const handleRightDrag = useCallback((clientX) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const pct = ((rect.right - clientX) / rect.width) * 100;
    setRightWidth(Math.max(15, Math.min(45, pct)));
  }, []);

  const centerWidth = 100 - leftWidth - rightWidth;

  return (
    <div className="h-screen flex flex-col bg-gray-50 overflow-hidden">
      {/* Top bar */}
      <IntentInput
        onSubmit={startPipeline}
        isRunning={isRunning}
        connected={connected}
      />

      {/* Main content */}
      <div ref={containerRef} className="flex-1 flex overflow-hidden">
        {/* Left: PRD Panel */}
        <div style={{ width: `${leftWidth}%` }} className="bg-white overflow-hidden flex-shrink-0">
          <PRDPanel content={prdContent} />
        </div>

        <ResizeHandle onDrag={handleLeftDrag} />

        {/* Center: DAG + Agent Feed */}
        <div style={{ width: `${centerWidth}%` }} className="flex flex-col min-w-0">
          <div className="h-[340px] border-b border-gray-200 bg-gray-50/50">
            <PipelineDAG tasks={tasks} />
          </div>
          <div className="flex-1 overflow-hidden bg-white">
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

        <ResizeHandle onDrag={handleRightDrag} />

        {/* Right: Artifact Explorer */}
        <div style={{ width: `${rightWidth}%` }} className="bg-white overflow-hidden flex-shrink-0">
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

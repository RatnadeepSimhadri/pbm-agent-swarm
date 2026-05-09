import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  fontFamily: 'Inter, system-ui, sans-serif',
  fontSize: 13,
  suppressErrorRendering: true,
});

let renderCounter = 0;

export function MermaidDiagram({ chart }) {
  const containerRef = useRef(null);
  const [svg, setSvg] = useState(null);
  const [pending, setPending] = useState(true);

  useEffect(() => {
    if (!chart) return;

    // Debounce: wait for content to stabilize (streaming sends chunks)
    setPending(true);
    const timer = setTimeout(async () => {
      const id = `mermaid-${++renderCounter}`;
      try {
        const result = await mermaid.render(id, chart.trim());
        setSvg(result.svg);
      } catch {
        setSvg(null);
      }
      // Clean up any error elements mermaid may have injected
      document.getElementById(id)?.remove();
      document.querySelector(`[data-id="${id}"]`)?.remove();
      setPending(false);
    }, 600);

    return () => clearTimeout(timer);
  }, [chart]);

  if (pending) {
    return (
      <div className="my-2 p-4 bg-gray-50 border border-gray-200 rounded-lg text-center">
        <div className="text-[11px] text-gray-400">Rendering diagram...</div>
      </div>
    );
  }

  if (!svg) {
    return (
      <pre className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-[11px] text-gray-600 font-mono overflow-x-auto my-2 whitespace-pre-wrap">
        {chart}
      </pre>
    );
  }

  return (
    <div
      ref={containerRef}
      className="my-2 p-3 bg-gray-50 border border-gray-200 rounded-lg overflow-x-auto [&_svg]:max-w-full [&_svg]:h-auto"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}

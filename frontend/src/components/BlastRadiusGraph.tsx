"use client";

import React, { useState, useMemo, useRef, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import type { ForceGraphMethods, LinkObject, NodeObject } from "react-force-graph-2d";
import { ZoomIn, RefreshCw, Route, Loader2 } from "lucide-react";
import { api } from "../lib/api";

// Load react-force-graph-2d dynamically with ssr: false to prevent Next.js build errors
const ForceGraph2D = dynamic(
  () => import("react-force-graph-2d").then((mod) => mod.default),
  { ssr: false }
);

export interface GraphNode {
  id: string;
  name: string;
  type: "file" | "class" | "function" | "api" | "vulnerability";
  severity?: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "none";
  val?: number; // size weight
}

export interface GraphLink {
  source: string;
  target: string;
  type: "CALLS" | "CONTAINS" | "IMPORTS" | "AFFECTS";
}

interface BlastRadiusGraphProps {
  nodes?: GraphNode[];
  links?: GraphLink[];
  vulnerabilityNodeId?: string;
  scanId?: string; // If provided, fetch real graph data from API
}

export default function BlastRadiusGraph({
  nodes: initialNodes = [],
  links: initialLinks = [],
  vulnerabilityNodeId,
  scanId,
}: BlastRadiusGraphProps) {
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>(initialNodes);
  const [graphLinks, setGraphLinks] = useState<GraphLink[]>(initialLinks);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch real graph data when scanId changes
  useEffect(() => {
    if (!scanId) {
      setGraphNodes(initialNodes);
      setGraphLinks(initialLinks);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .blastRadius(scanId)
      .then((data) => {
        if (cancelled) return;
        setGraphNodes(data.nodes || []);
        setGraphLinks(data.links || []);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message || "Failed to load graph");
        // Fallback to initial data if fetch fails
        setGraphNodes(initialNodes);
        setGraphLinks(initialLinks);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [scanId, initialNodes, initialLinks]);

  return (
    <GraphCanvas
      nodes={graphNodes}
      links={graphLinks}
      vulnerabilityNodeId={vulnerabilityNodeId}
      loading={loading}
      error={error}
    />
  );
}

interface GraphCanvasProps {
  nodes: GraphNode[];
  links: GraphLink[];
  vulnerabilityNodeId?: string;
  loading: boolean;
  error: string | null;
}

function GraphCanvas({ nodes, links, vulnerabilityNodeId, loading, error }: GraphCanvasProps) {
  const fgRef = useRef<ForceGraphMethods | undefined>(undefined);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });
  const [selectedNode, setSelectedNode] = useState<string | null>(vulnerabilityNodeId || null);
  const [highlightNodes, setHighlightNodes] = useState<Set<string>>(new Set());
  const [highlightLinks, setHighlightLinks] = useState<Set<string>>(new Set());

  const linkNodeId = (endpoint: unknown) =>
    typeof endpoint === "object" && endpoint !== null && "id" in endpoint
      ? String((endpoint as { id?: string | number }).id)
      : String(endpoint);

  const calculateBlastRadius = useCallback(
    (startNodeId: string) => {
      const reachable = new Set<string>([startNodeId]);
      const activeLinks = new Set<string>();
      const queue = [startNodeId];
      while (queue.length > 0) {
        const current = queue.shift()!;
        links.forEach((link) => {
          const sourceId = linkNodeId(link.source);
          const targetId = linkNodeId(link.target);
          if (sourceId === current && !reachable.has(targetId)) {
            reachable.add(targetId);
            activeLinks.add(`${sourceId}->${targetId}`);
            queue.push(targetId);
          }
        });
      }
      return { reachable, activeLinks };
    },
    [links]
  );

  useEffect(() => {
    if (vulnerabilityNodeId) {
      const radius = calculateBlastRadius(vulnerabilityNodeId);
      setHighlightNodes(radius.reachable);
      setHighlightLinks(radius.activeLinks);
    } else {
      setHighlightNodes(new Set());
      setHighlightLinks(new Set());
    }
  }, [vulnerabilityNodeId, calculateBlastRadius]);

  const getNodeColor = (node: GraphNode, isHighlighted: boolean) => {
    if (selectedNode && !isHighlighted && node.id !== selectedNode) {
      return "rgba(90, 94, 79, 0.18)";
    }
    if (node.id === selectedNode) return "#ff655d";
    switch (node.type) {
      case "vulnerability":
        return "#ff655d";
      case "api":
        return "#ffc857";
      case "function":
        return "#c7f36b";
      case "class":
        return "#58c7b8";
      case "file":
        return "#a6a99a";
      default:
        return "#c7f36b";
    }
  };

  const handleNodeClick = (rawNode: NodeObject) => {
    const node = rawNode as GraphNode & { x: number; y: number };
    if (selectedNode === node.id) {
      setSelectedNode(null);
      setHighlightNodes(new Set());
      setHighlightLinks(new Set());
    } else {
      setSelectedNode(node.id);
      const radius = calculateBlastRadius(node.id);
      setHighlightNodes(radius.reachable);
      setHighlightLinks(radius.activeLinks);
      if (fgRef.current) {
        fgRef.current.centerAt(node.x, node.y, 400);
        fgRef.current.zoom(2.5, 400);
      }
    }
  };

  const handleReset = () => {
    setSelectedNode(null);
    setHighlightNodes(new Set());
    setHighlightLinks(new Set());
    if (fgRef.current) {
      fgRef.current.zoomToFit(400, 30);
    }
  };

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;
    const observer = new ResizeObserver(([entry]) => {
      setDimensions({
        width: Math.max(320, Math.floor(entry.contentRect.width)),
        height: Math.max(320, Math.floor(entry.contentRect.height)),
      });
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const graphData = useMemo(() => {
    return {
      nodes: nodes.map((n) => ({ ...n, val: n.type === "vulnerability" ? 15 : n.type === "api" ? 12 : 8 })),
      links: links.map((l) => ({ ...l })),
    };
  }, [nodes, links]);

  return (
    <div className="glass-panel rounded-xl overflow-hidden relative flex flex-col h-full min-h-[350px]">
      {/* Top control bar */}
      <div className="absolute top-4 left-4 z-10 flex gap-2">
        <button
          onClick={handleReset}
          className="p-2 bg-[#11130e]/90 hover:bg-[#1b1f16] border border-white/10 rounded-lg text-slate-400 hover:text-primary transition-colors"
          title="Reset View"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
        <button
          onClick={() => fgRef.current?.zoomToFit(400, 30)}
          className="p-2 bg-[#11130e]/90 hover:bg-[#1b1f16] border border-white/10 rounded-lg text-slate-400 hover:text-primary transition-colors"
          title="Fit to screen"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
      </div>

      {/* Loading overlay */}
      {loading && (
        <div className="absolute inset-0 z-20 bg-[#090a08]/80 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      )}

      {/* Error overlay */}
      {error && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 bg-rose-500/10 border border-rose-500/20 text-rose-400 px-4 py-2 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Legend overlay */}
      <div className="absolute top-4 right-4 z-10 bg-[#0c0e0a]/90 border border-white/10 p-3 rounded-lg text-xs font-mono flex flex-col gap-2 pointer-events-none">
        <div className="text-[10px] text-slate-500 font-bold uppercase pb-1 border-b border-white/5">
          Entity map
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rotate-45 bg-[#ff655d]" />
          <span className="text-slate-300">Vulnerability</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#ffc857]" />
          <span className="text-slate-300">API Endpoint</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#c7f36b]" />
          <span className="text-slate-300">Function (Logic)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#58c7b8]" />
          <span className="text-slate-300">Class (Module)</span>
        </div>
      </div>

      {/* Interactive canvas viewport */}
      <div ref={containerRef} className="flex-1 relative overflow-hidden bg-[#090a08]">
        <div className="graph-scan-line pointer-events-none absolute inset-x-0 top-0 z-[1] h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent" />
        {graphData.nodes.length > 0 && (
          <ForceGraph2D
            ref={fgRef}
            width={dimensions.width}
            height={dimensions.height}
            graphData={graphData}
            nodeLabel={(rawNode: NodeObject) => {
              const node = rawNode as GraphNode & { x: number; y: number };
              return `${node.type.toUpperCase()}: ${node.name}`;
            }}
            nodeColor={(rawNode: NodeObject) => {
              const node = rawNode as GraphNode;
              return getNodeColor(node, highlightNodes.has(node.id));
            }}
            nodeVal={(rawNode: NodeObject) => (rawNode as GraphNode).val || 8}
            linkWidth={(link: LinkObject) => {
              const sourceId = linkNodeId(link.source);
              const targetId = linkNodeId(link.target);
              return highlightLinks.has(`${sourceId}->${targetId}`) ? 2.4 : 0.8;
            }}
            linkColor={(link: LinkObject) => {
              const sourceId = linkNodeId(link.source);
              const targetId = linkNodeId(link.target);
              if (highlightLinks.has(`${sourceId}->${targetId}`)) {
                return "#ff655d";
              }
              return "rgba(243, 242, 233, 0.12)";
            }}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={0.92}
            linkDirectionalParticles={2}
            linkDirectionalParticleSpeed={0.004}
            linkDirectionalParticleWidth={(link: LinkObject) => {
              const sourceId = linkNodeId(link.source);
              const targetId = linkNodeId(link.target);
              return highlightLinks.has(`${sourceId}->${targetId}`) ? 2.4 : 0;
            }}
            linkDirectionalParticleColor={() => "#ff655d"}
            onNodeClick={handleNodeClick}
            cooldownTicks={70}
            d3AlphaDecay={0.045}
            d3VelocityDecay={0.32}
            backgroundColor="#090a08"
            nodeCanvasObject={(rawNode: NodeObject, ctx, globalScale) => {
              const node = rawNode as GraphNode & { x: number; y: number; val: number };
              const label = node.name;
              const fontSize = 11 / globalScale;
              const x = node.x ?? 0;
              const y = node.y ?? 0;
              ctx.font = `${fontSize}px monospace`;
              const r = node.val;
              ctx.save();
              ctx.shadowBlur = selectedNode === node.id ? 18 : 8;
              ctx.shadowColor = getNodeColor(node, highlightNodes.has(node.id));
              ctx.beginPath();
              if (node.type === "vulnerability") {
                ctx.rect(x - r * 0.72, y - r * 0.72, r * 1.44, r * 1.44);
              } else if (node.type === "file") {
                ctx.roundRect(x - r * 0.8, y - r * 0.65, r * 1.6, r * 1.3, 2);
              } else {
                ctx.arc(x, y, r, 0, 2 * Math.PI, false);
              }
              ctx.fillStyle = getNodeColor(node, highlightNodes.has(node.id));
              ctx.fill();
              ctx.restore();

              if (selectedNode === node.id || (node.type === "vulnerability" && !selectedNode)) {
                ctx.beginPath();
                ctx.arc(x, y, r + 4, 0, 2 * Math.PI, false);
                ctx.strokeStyle = "rgba(255, 101, 93, 0.75)";
                ctx.lineWidth = 2 / globalScale;
                ctx.stroke();
              }

              if (globalScale > 1.2 || selectedNode === node.id) {
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillStyle = "rgba(243, 242, 233, 0.95)";
                ctx.fillText(label, x, y + r + 6);
              }
            }}
          />
        )}
      </div>

      {/* Downstream Blast Radius Info Bar */}
      {selectedNode && (
        <div className="p-4 bg-[#0c0e0a] border-t border-white/8 flex items-center justify-between animate-slide-up">
          <div className="flex items-center gap-3">
            <div className="bg-accent/10 p-2 rounded border border-accent/20 text-accent">
              <Route className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-slate-500 font-mono">SELECTED NODE IMPACT</div>
              <div className="text-sm font-semibold text-slate-200">
                Blast radius: <span className="text-accent font-mono">{highlightNodes.size} nodes</span> downstream
              </div>
            </div>
          </div>
          <div className="text-xs text-slate-400 font-mono italic max-w-md text-right">
            Select any entity to trace downstream impact.
          </div>
        </div>
      )}
    </div>
  );
}

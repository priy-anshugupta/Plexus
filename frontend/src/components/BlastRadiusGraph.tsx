"use client";

import React, { useState, useMemo, useRef } from "react";
import dynamic from "next/dynamic";
import { useRole } from "../context/RoleContext";
import { AlertTriangle, Focus, ZoomIn, RefreshCw } from "lucide-react";

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
  nodes: GraphNode[];
  links: GraphLink[];
  vulnerabilityNodeId?: string;
}

export default function BlastRadiusGraph({
  nodes,
  links,
  vulnerabilityNodeId,
}: BlastRadiusGraphProps) {
  const fgRef = useRef<any>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(vulnerabilityNodeId || null);
  const [highlightNodes, setHighlightNodes] = useState<Set<string>>(new Set());
  const [highlightLinks, setHighlightLinks] = useState<Set<string>>(new Set());

  // Generate node colors based on type and severity
  const getNodeColor = (node: GraphNode, isHighlighted: boolean) => {
    if (selectedNode && !isHighlighted && node.id !== selectedNode) {
      return "rgba(50, 60, 80, 0.15)"; // faded out
    }

    if (node.id === selectedNode) return "#f43f5e"; // hot rose for selected

    switch (node.type) {
      case "vulnerability":
        return "#ff3366";
      case "api":
        return "#f97316"; // orange
      case "function":
        return "#3b82f6"; // blue
      case "class":
        return "#a855f7"; // purple
      case "file":
        return "#94a3b8"; // grey
      default:
        return "#10b981";
    }
  };

  // Perform BFS traversal to compute downstream blast radius
  const computeBlastRadius = (startNodeId: string) => {
    const reachable = new Set<string>([startNodeId]);
    const queue = [startNodeId];
    const activeLinks = new Set<string>();

    while (queue.length > 0) {
      const current = queue.shift()!;
      // Find all links originating from the current node (downstream calls)
      links.forEach((link) => {
        // Link source/target can be objects or strings depending on react-force-graph internal parsing
        const sourceId = typeof link.source === "object" ? (link.source as any).id : link.source;
        const targetId = typeof link.target === "object" ? (link.target as any).id : link.target;

        if (sourceId === current && !reachable.has(targetId)) {
          reachable.add(targetId);
          activeLinks.add(`${sourceId}->${targetId}`);
          queue.push(targetId);
        }
      });
    }

    setHighlightNodes(reachable);
    setHighlightLinks(activeLinks);
  };

  const handleNodeClick = (node: any) => {
    if (selectedNode === node.id) {
      // Toggle off
      setSelectedNode(null);
      setHighlightNodes(new Set());
      setHighlightLinks(new Set());
    } else {
      setSelectedNode(node.id);
      computeBlastRadius(node.id);
      // Center camera on node
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

  // Memoize graph data to avoid recalculations
  const graphData = useMemo(() => {
    return {
      nodes: nodes.map((n) => ({ ...n, val: n.type === "vulnerability" ? 15 : n.type === "api" ? 12 : 8 })),
      links: links.map((l) => ({ ...l })),
    };
  }, [nodes, links]);

  return (
    <div className="glass-panel rounded-xl overflow-hidden relative flex flex-col h-[500px]">
      {/* Top control bar */}
      <div className="absolute top-4 left-4 z-10 flex gap-2">
        <button
          onClick={handleReset}
          className="p-2 bg-slate-900/80 hover:bg-slate-800 border border-white/5 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
          title="Reset View"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
        <button
          onClick={() => fgRef.current?.zoomToFit(400, 30)}
          className="p-2 bg-slate-900/80 hover:bg-slate-800 border border-white/5 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
          title="Fit to screen"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
      </div>

      {/* Legend overlay */}
      <div className="absolute top-4 right-4 z-10 bg-slate-950/80 border border-white/5 p-3 rounded-lg text-xs font-mono flex flex-col gap-2 pointer-events-none">
        <div className="text-[10px] text-slate-500 font-bold uppercase pb-1 border-b border-white/5">
          Graph Legend
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#ff3366]" />
          <span className="text-slate-300">Vulnerability</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#f97316]" />
          <span className="text-slate-300">API Endpoint</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#3b82f6]" />
          <span className="text-slate-300">Function (Logic)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#a855f7]" />
          <span className="text-slate-300">Class (Module)</span>
        </div>
      </div>

      {/* Interactive canvas viewport */}
      <div className="flex-1 bg-[#06080c]">
        {graphData.nodes.length > 0 && (
          <ForceGraph2D
            ref={fgRef}
            graphData={graphData}
            nodeLabel={(node: any) => `${node.type.toUpperCase()}: ${node.name}`}
            nodeColor={(node: any) => getNodeColor(node as GraphNode, highlightNodes.has(node.id))}
            nodeVal={(node: any) => node.val}
            linkWidth={(link: any) => {
              const sourceId = typeof link.source === "object" ? link.source.id : link.source;
              const targetId = typeof link.target === "object" ? link.target.id : link.target;
              return highlightLinks.has(`${sourceId}->${targetId}`) ? 3 : 1.2;
            }}
            linkColor={(link: any) => {
              const sourceId = typeof link.source === "object" ? link.source.id : link.source;
              const targetId = typeof link.target === "object" ? link.target.id : link.target;
              if (highlightLinks.has(`${sourceId}->${targetId}`)) {
                return "#ff3366"; // red for active propagation path
              }
              return "rgba(255, 255, 255, 0.08)";
            }}
            linkDirectionalParticles={4}
            linkDirectionalParticleWidth={(link: any) => {
              const sourceId = typeof link.source === "object" ? link.source.id : link.source;
              const targetId = typeof link.target === "object" ? link.target.id : link.target;
              return highlightLinks.has(`${sourceId}->${targetId}`) ? 3.5 : 0;
            }}
            linkDirectionalParticleColor={() => "#ff3366"}
            onNodeClick={handleNodeClick}
            cooldownTicks={100}
            nodeCanvasObject={(node: any, ctx, globalScale) => {
              const label = node.name;
              const fontSize = 11 / globalScale;
              ctx.font = `${fontSize}px var(--font-mono), monospace`;
              
              // Draw node circle
              const r = node.val;
              ctx.beginPath();
              ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
              ctx.fillStyle = getNodeColor(node as GraphNode, highlightNodes.has(node.id));
              ctx.fill();

              // Add a glow ring to the selected node
              if (selectedNode === node.id || (node.type === "vulnerability" && !selectedNode)) {
                ctx.beginPath();
                ctx.arc(node.x, node.y, r + 4, 0, 2 * Math.PI, false);
                ctx.strokeStyle = "rgba(244, 63, 94, 0.6)";
                ctx.lineWidth = 2 / globalScale;
                ctx.stroke();
              }

              // Text labeling (only show if zoom is close enough or node is selected)
              if (globalScale > 1.2 || selectedNode === node.id) {
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillStyle = "rgba(241, 245, 249, 0.95)";
                ctx.fillText(label, node.x, node.y + r + 6);
              }
            }}
          />
        )}
      </div>

      {/* Downstream Blast Radius Info Bar */}
      {selectedNode && (
        <div className="p-4 bg-slate-950 border-t border-white/5 flex items-center justify-between animate-slide-up">
          <div className="flex items-center gap-3">
            <div className="bg-rose-500/10 p-2 rounded border border-rose-500/20 text-rose-500">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-slate-500 font-mono">SELECTED NODE IMPACT</div>
              <div className="text-sm font-semibold text-slate-200">
                Blast Radius includes: <span className="text-rose-400 font-mono">{highlightNodes.size} nodes</span> downstream
              </div>
            </div>
          </div>
          <div className="text-xs text-slate-400 font-mono italic max-w-md text-right">
            Click another node or use the reset button to recalculate the blast radius.
          </div>
        </div>
      )}
    </div>
  );
}

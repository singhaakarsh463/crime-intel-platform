import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as d3 from "d3";
import { fetchNetworkGraph } from "../lib/api.js";

const SEVERITY_COLOR = {
  low: "#3FD6C1",
  medium: "#F0A202",
  high: "#E8833A",
  critical: "#E23D5B",
};

export default function NetworkGraph() {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const navigate = useNavigate();
  const [graph, setGraph] = useState({ nodes: [], edges: [], recurring_links: 0 });
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    fetchNetworkGraph()
      .then(setGraph)
      .catch(() => setError("Could not load the network graph. Is the API running?"));
  }, []);

  useEffect(() => {
    if (!graph.nodes.length || !svgRef.current) return;

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const nodes = graph.nodes.map((n) => ({ ...n }));
    const nodeById = new Map(nodes.map((n) => [n.id, n]));
    const links = graph.edges
      .filter((e) => nodeById.has(e.source) && nodeById.has(e.target))
      .map((e) => ({ ...e }));

    const g = svg.append("g");

    svg.call(
      d3.zoom().scaleExtent([0.3, 3]).on("zoom", (event) => {
        g.attr("transform", event.transform);
      })
    );

    const simulation = d3
      .forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d) => d.id).distance((l) => (l.kind === "shared_phone" ? 90 : 60)))
      .force("charge", d3.forceManyBody().strength(-140))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide().radius(22));

    const link = g
      .append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", (d) => (d.kind === "shared_phone" ? "#E23D5B" : "#232E42"))
      .attr("stroke-width", (d) => (d.kind === "shared_phone" ? 2 : 1))
      .attr("stroke-dasharray", (d) => (d.kind === "shared_phone" ? "4,3" : "none"))
      .attr("opacity", 0.8);

    const node = g
      .append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .style("cursor", "pointer")
      .call(
        d3
          .drag()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      )
      .on("click", (_, d) => setSelected(d));

    node
      .filter((d) => d.type === "case")
      .append("rect")
      .attr("x", -8)
      .attr("y", -8)
      .attr("width", 16)
      .attr("height", 16)
      .attr("rx", 3)
      .attr("fill", (d) => SEVERITY_COLOR[d.severity] || "#7C8AA3")
      .attr("stroke", "#0B0F17")
      .attr("stroke-width", 1.5);

    node
      .filter((d) => d.type === "person")
      .append("circle")
      .attr("r", 6)
      .attr("fill", "#F0A202")
      .attr("stroke", "#0B0F17")
      .attr("stroke-width", 1.5);

    node
      .append("text")
      .text((d) => d.label)
      .attr("x", 12)
      .attr("y", 4)
      .attr("font-size", 10)
      .attr("font-family", "JetBrains Mono, monospace")
      .attr("fill", "#7C8AA3");

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);
      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    return () => simulation.stop();
  }, [graph]);

  return (
    <div className="p-8 h-screen flex flex-col">
      <div className="mb-4 flex items-start justify-between flex-wrap gap-3">
        <div>
          <p className="font-mono text-teal text-xs tracking-[0.3em] mb-1">RELATIONSHIPS</p>
          <h2 className="font-display text-3xl text-ink">Case &amp; Suspect Network</h2>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono text-muted">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-teal inline-block" /> Case
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-amber inline-block" /> Person
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-4 border-t-2 border-crit border-dashed inline-block" /> Shared phone number
            ({graph.recurring_links})
          </div>
        </div>
      </div>

      {error && (
        <p className="text-crit text-sm font-mono border border-crit/40 bg-crit/10 rounded px-4 py-3 mb-4">
          {error}
        </p>
      )}

      <div className="flex-1 flex gap-4 min-h-0">
        <div ref={containerRef} className="flex-1 border border-line rounded-md overflow-hidden bg-panel">
          <svg ref={svgRef} width="100%" height="100%" />
        </div>

        {selected && (
          <div className="w-72 bg-panel border border-line rounded-md p-4 shrink-0">
            <p className="font-mono text-xs text-muted uppercase mb-1">{selected.type}</p>
            <p className="text-ink font-display text-xl mb-1">{selected.label}</p>
            <p className="text-muted text-sm mb-3">{selected.sublabel}</p>
            {selected.phone && (
              <p className="text-xs font-mono text-teal mb-3">{selected.phone}</p>
            )}
            {selected.district && (
              <p className="text-xs text-muted mb-3">District: {selected.district}</p>
            )}
            <button
              onClick={() => navigate(`/cases/${selected.ref_id}`)}
              className="text-xs font-mono text-amber hover:underline"
            >
              View case →
            </button>
          </div>
        )}
      </div>
      <p className="text-muted text-xs font-mono mt-2">
        {graph.nodes.length} node(s), drag to reposition, scroll to zoom, click a node for details.
      </p>
    </div>
  );
}

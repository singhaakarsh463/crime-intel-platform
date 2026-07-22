import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as d3 from "d3";
import { fetchNetworkGraph, fetchNetworkGroups } from "../lib/api.js";

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
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    fetchNetworkGraph()
      .then(setGraph)
      .catch(() => setError("Could not load the network graph. Is the API running?"));
    fetchNetworkGroups()
      .then(setGroups)
      .catch(() => setGroups([]));
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
      .enter()
      .append("line")
      .attr("stroke", (d) => (d.kind === "shared_phone" ? "#E23D5B" : d.kind === "financial_transfer" ? "#F0A202" : "#243242"))
      .attr("stroke-dasharray", (d) => (d.kind === "shared_phone" ? "4,3" : "none"))
      .attr("stroke-width", (d) => (d.kind === "shared_phone" ? 2 : d.kind === "financial_transfer" ? 2.5 : 1));

    const nodeGroup = g
      .append("g")
      .selectAll("g")
      .data(nodes)
      .enter()
      .append("g")
      .style("cursor", "pointer")
      .on("click", (event, d) => {
        event.stopPropagation();
        if (d.type === "case") navigate(`/cases/${d.ref_id}`);
        else setSelected(d);
      });

    // Check if node belongs to selectedGroup
    const selectedGroupMemberIds = selectedGroup
      ? new Set(selectedGroup.members.map((m) => m.person_node_id))
      : null;

    nodeGroup
      .append("circle")
      .attr("r", (d) => (d.type === "case" ? 14 : d.type === "account" ? 10 : 8))
      .attr("fill", (d) => {
        if (selectedGroupMemberIds && selectedGroupMemberIds.has(d.id)) return "#F0A202";
        if (d.type === "case") return SEVERITY_COLOR[d.severity] || "#3FD6C1";
        if (d.type === "account") return "#3FD6C1";
        return "#5B6B7C";
      })
      .attr("stroke", (d) => (selectedGroupMemberIds && selectedGroupMemberIds.has(d.id) ? "#E23D5B" : "#0F172A"))
      .attr("stroke-width", (d) => (selectedGroupMemberIds && selectedGroupMemberIds.has(d.id) ? 3 : 2));

    nodeGroup
      .append("text")
      .text((d) => d.label)
      .attr("x", 12)
      .attr("y", 4)
      .attr("fill", "#F1F5F9")
      .attr("font-size", "10px")
      .attr("font-family", "monospace");

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      nodeGroup.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    return () => simulation.stop();
  }, [graph, selectedGroup, navigate]);

  return (
    <div className="flex h-screen bg-bg text-ink">
      <div className="flex-1 relative flex flex-col">
        <div className="p-4 border-b border-line flex items-center justify-between bg-panel">
          <div>
            <h2 className="font-display text-xl">Criminal & Financial Network Graph</h2>
            <p className="text-muted text-xs font-mono">
              Dashed red edges = shared phone number across cases &middot; Yellow edges = financial transfers
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-teal" /> Case
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#5B6B7C]" /> Person
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber" /> Flagged Gang Member
            </span>
          </div>
        </div>

        <div ref={containerRef} className="flex-1 w-full relative overflow-hidden bg-bg">
          {error && (
            <div className="absolute top-4 left-4 z-10 text-crit text-xs font-mono bg-crit/10 border border-crit/40 px-3 py-2 rounded">
              {error}
            </div>
          )}
          <svg ref={svgRef} className="w-full h-full" />
        </div>
      </div>

      {/* Sidebar Panel for Gang Groups & Node Details */}
      <div className="w-80 border-l border-line bg-panel p-4 flex flex-col space-y-6 overflow-y-auto">
        <div>
          <h3 className="font-display text-lg mb-1">Detected Syndicates ({groups.length})</h3>
          <p className="text-muted text-[11px] font-mono mb-3">
            Connected clusters sharing multiple link vectors
          </p>

          {groups.length === 0 ? (
            <p className="text-muted text-xs font-mono">No qualifying gang clusters detected.</p>
          ) : (
            <div className="space-y-2">
              {groups.map((g) => (
                <div
                  key={g.group_id}
                  onClick={() => setSelectedGroup(selectedGroup?.group_id === g.group_id ? null : g)}
                  className={`border rounded p-3 text-xs font-mono cursor-pointer transition ${
                    selectedGroup?.group_id === g.group_id
                      ? "bg-amber/10 border-amber text-amber"
                      : "bg-panel2 border-line text-ink hover:border-teal"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold">{g.name}</span>
                    <span className="px-1.5 py-0.5 rounded bg-crit/10 text-crit border border-crit/40 text-[10px]">
                      Risk: {g.group_risk_score}
                    </span>
                  </div>
                  <p className="text-muted text-[11px]">
                    Members: {g.member_count} &middot; Cases: {g.linked_cases}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {selected && (
          <div className="border-t border-line pt-4">
            <h4 className="font-display text-base text-teal mb-2">Node Details</h4>
            <div className="bg-panel2 border border-line rounded p-3 text-xs font-mono space-y-1">
              <p className="text-ink font-semibold">{selected.label}</p>
              <p className="text-muted">{selected.sublabel}</p>
              {selected.phone && <p className="text-teal">{selected.phone}</p>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

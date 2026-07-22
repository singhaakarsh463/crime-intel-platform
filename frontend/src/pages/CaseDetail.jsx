import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api, { fetchSimilarCases } from "../lib/api.js";

const SEVERITY_COLOR = {
  low: "#3FD6C1",
  medium: "#F0A202",
  high: "#E8833A",
  critical: "#E23D5B",
};

export default function CaseDetail() {
  const { id } = useParams();
  const [caseData, setCaseData] = useState(null);
  const [similarCases, setSimilarCases] = useState([]);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    api
      .get(`/cases/${id}`)
      .then(({ data }) => setCaseData(data))
      .catch(() => setError("Could not load this case. It may not exist or the API is down."));
    fetchSimilarCases(id).then(setSimilarCases).catch(() => setSimilarCases([]));
  }, [id]);

  async function handleExport() {
    setExporting(true);
    try {
      const response = await api.get(`/export/cases/${id}/report`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${caseData.case_id}_report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError("Could not generate the PDF report.");
    } finally {
      setExporting(false);
    }
  }

  if (error) {
    return (
      <div className="p-8">
        <p className="text-crit text-sm font-mono border border-crit/40 bg-crit/10 rounded px-4 py-3">
          {error}
        </p>
        <Link to="/cases" className="text-teal text-sm hover:underline mt-4 inline-block">
          ← Back to case search
        </Link>
      </div>
    );
  }

  if (!caseData) {
    return <div className="p-8 text-muted text-sm">Loading case...</div>;
  }

  return (
    <div className="p-8 max-w-4xl">
      <Link to="/cases" className="text-muted text-xs font-mono hover:text-teal transition">
        ← BACK TO CASE SEARCH
      </Link>

      <div className="flex items-start justify-between mt-3 mb-6">
        <div>
          <p className="font-mono text-teal text-xs tracking-[0.2em] mb-1">{caseData.case_id}</p>
          <h2 className="font-display text-3xl text-ink">{caseData.title}</h2>
        </div>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="bg-amber text-base font-semibold rounded px-4 py-2 text-sm hover:brightness-110 transition disabled:opacity-50 whitespace-nowrap"
        >
          {exporting ? "Generating..." : "⬇ Export PDF Report"}
        </button>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-6">
        <Field label="District" value={caseData.district} />
        <Field label="Station" value={caseData.station_name} />
        <Field label="Crime Type" value={caseData.crime_type} />
        <Field label="Incident Date" value={new Date(caseData.incident_date).toLocaleDateString()} />
      </div>

      <div className="flex gap-3 mb-6">
        <span className="text-xs font-mono uppercase px-3 py-1.5 rounded bg-panel2 text-ink border border-line">
          {caseData.status.replace("_", " ")}
        </span>
        <span
          className="text-xs font-mono uppercase px-3 py-1.5 rounded"
          style={{
            color: SEVERITY_COLOR[caseData.severity],
            border: `1px solid ${SEVERITY_COLOR[caseData.severity]}55`,
            background: `${SEVERITY_COLOR[caseData.severity]}11`,
          }}
        >
          {caseData.severity} severity
        </span>
      </div>

      <Section title="Summary">
        <p className="text-ink text-sm leading-relaxed">{caseData.summary || "No summary recorded."}</p>
      </Section>

      <Section title={`Persons of Interest (${caseData.persons.length})`}>
        {caseData.persons.length === 0 ? (
          <p className="text-muted text-sm">No persons linked to this case yet.</p>
        ) : (
          <div className="space-y-2">
            {caseData.persons.map((p) => (
              <div key={p.id} className="border border-line rounded px-4 py-3 bg-panel2 flex justify-between">
                <div>
                  <p className="text-ink text-sm">{p.name}</p>
                  <p className="text-muted text-xs font-mono capitalize">{p.role_in_case}</p>
                </div>
                <p className="text-muted text-xs font-mono">{p.phone_number}</p>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title={`Evidence Log (${caseData.evidence.length})`}>
        {caseData.evidence.length === 0 ? (
          <p className="text-muted text-sm">No evidence recorded yet.</p>
        ) : (
          <div className="space-y-2">
            {caseData.evidence.map((e) => (
              <div key={e.id} className="border border-line rounded px-4 py-3 bg-panel2 flex justify-between">
                <p className="text-ink text-sm">{e.description}</p>
                <p className="text-muted text-xs font-mono truncate max-w-[200px]">{e.evidence_hash}</p>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title="Similar Cases">
        {similarCases.length === 0 ? (
          <p className="text-muted text-sm">No sufficiently similar cases found yet.</p>
        ) : (
          <div className="space-y-2">
            {similarCases.map((sc) => (
              <Link
                key={sc.id}
                to={`/cases/${sc.id}`}
                className="flex items-center justify-between border border-line rounded px-4 py-3 bg-panel2 hover:border-teal transition"
              >
                <div>
                  <p className="font-mono text-xs text-muted">{sc.case_id}</p>
                  <p className="text-ink text-sm">{sc.title}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-muted text-xs">{sc.district}</span>
                  <span className="text-teal text-xs font-mono">{(sc.similarity * 100).toFixed(0)}% match</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div className="bg-panel border border-line rounded-md px-4 py-3">
      <p className="text-muted text-xs font-mono uppercase mb-1">{label}</p>
      <p className="text-ink text-sm">{value}</p>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="mb-6">
      <p className="text-ink font-display text-xl mb-3">{title}</p>
      {children}
    </div>
  );
}

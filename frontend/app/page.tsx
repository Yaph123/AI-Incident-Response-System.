import { fetchIncidents, type Incident } from "../lib/api";

function statusClass(status: string): string {
  if (status === "open") return "bg-rose-500/20 text-rose-300";
  if (status === "investigating") return "bg-amber-500/20 text-amber-200";
  if (status === "resolved") return "bg-emerald-500/20 text-emerald-200";
  return "bg-slate-700 text-slate-200";
}

export default async function HomePage() {
  let incidents: Incident[] = [];
  let error = "";
  try {
    incidents = await fetchIncidents();
  } catch (err) {
    error = err instanceof Error ? err.message : "Unknown error";
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">AI Incident Response Dashboard</h1>
        <p className="mt-2 text-slate-400">
          Monitor active incidents, AI summaries, and operational context.
        </p>
      </header>

      {error ? (
        <div className="rounded border border-rose-500/40 bg-rose-500/10 p-4 text-rose-100">
          Could not load incidents: {error}
        </div>
      ) : (
        <section className="space-y-4">
          {incidents.length === 0 ? (
            <div className="rounded border border-slate-800 bg-slate-900 p-6 text-slate-400">
              No incidents yet. Send a webhook alert to start the pipeline.
            </div>
          ) : (
            incidents.map((incident) => (
              <article key={incident.id} className="rounded border border-slate-800 bg-slate-900 p-5">
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-xl font-semibold">{incident.title}</h2>
                  <span className={`rounded px-2 py-1 text-xs font-medium ${statusClass(incident.status)}`}>
                    {incident.status}
                  </span>
                </div>
                <p className="text-sm text-slate-300">{incident.description || "No description provided."}</p>
                <div className="mt-3 text-xs text-slate-400">
                  Severity: <span className="font-semibold text-slate-200">{incident.severity}</span>
                </div>
                <div className="mt-2 text-sm text-slate-300">
                  {incident.ai_summary ? incident.ai_summary.slice(0, 260) : "AI summary pending..."}
                </div>
              </article>
            ))
          )}
        </section>
      )}
    </main>
  );
}

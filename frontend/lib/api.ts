export type Incident = {
  id: string;
  title: string;
  description?: string;
  status: string;
  severity: string;
  ai_summary?: string;
  created_at: string;
};

const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function fetchIncidents(): Promise<Incident[]> {
  const response = await fetch(`${baseUrl}/api/incidents`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to fetch incidents: ${response.status}`);
  }
  return response.json();
}

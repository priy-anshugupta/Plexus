const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail || res.statusText);
  }
  return res.json() as Promise<T>;
}

export interface Scan {
  id: string;
  repository_id: string;
  scan_type: string;
  status: string;
  branch: string | null;
  commit_sha: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  total_findings: number;
  error_message: string | null;
}

export interface ScanListResponse {
  items: Scan[];
  total: number;
  page: number;
  page_size: number;
}

export interface Finding {
  id: string;
  scan_id: string;
  file_path: string;
  line_start: number;
  line_end: number;
  severity: string;
  category: string;
  title: string;
  description: string;
  suggestion: string;
  code_snippet: string;
  rule_id: string | null;
  confidence_score: number;
  is_ai_generated: boolean;
}

export interface Repository {
  id: string;
  name: string;
  full_name: string;
  clone_url: string;
  last_scanned_at: string | null;
}

export const api = {
  // Scans
  listScans: (page = 1, pageSize = 20) =>
    request<ScanListResponse>(`/scans?page=${page}&page_size=${pageSize}`),
  getScan: (id: string) => request<Scan>(`/scans/${id}`),
  triggerScan: (repoId: string, scanType: "full" | "incremental" = "full", branch?: string) =>
    request<Scan>("/scans", {
      method: "POST",
      body: JSON.stringify({ repository_id: repoId, scan_type: scanType, branch }),
    }),
  cancelScan: (id: string) => request<Scan>(`/scans/${id}/cancel`, { method: "POST" }),

  // Findings
  listFindings: (scanId?: string) =>
    request<{ items: Finding[]; total: number }>(`/findings${scanId ? `?scan_id=${scanId}` : ""}`),

  // Repositories
  listRepositories: () => request<{ items: Repository[]; total: number }>("/repositories"),
  connectRepo: (data: { name: string; clone_url: string }) =>
    request<Repository>("/repositories", { method: "POST", body: JSON.stringify(data) }),

  // Graph
  blastRadius: (scanId: string) =>
    request<{ nodes: any[]; links: any[] }>(`/graph/blast-radius/${scanId}`),

  // Health
  health: () => request<{ status: string; databases: Record<string, string> }>("/health"),
};

export function streamScanEvents(scanId: string, onEvent: (data: any) => void, onError?: (err: Event) => void): () => void {
  const url = `${API_BASE}/scans/${scanId}/stream`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onEvent(data);
      if (data.event === "completed" || data.event === "failed" || data.event === "cancelled") {
        eventSource.close();
      }
    } catch {
      onEvent({ event: "raw", data: event.data });
    }
  };

  eventSource.onerror = (err) => {
    if (onError) onError(err);
    eventSource.close();
  };

  return () => eventSource.close();
}

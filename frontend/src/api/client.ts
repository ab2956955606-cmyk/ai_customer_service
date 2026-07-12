export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001';

export type EvalLocale = 'en' | 'zh';

export type Ticket = {
  id: number;
  subject: string;
  description: string;
  customer_email: string | null;
  category: string | null;
  priority: string | null;
  risk_level: string | null;
  status: string;
  assigned_agent: string | null;
  final_response: string | null;
  created_at: string;
  updated_at: string;
};

export type Citation = {
  title: string;
  snippet: string;
  score: number;
};

export type AgentRun = {
  id: number;
  ticket_id: number;
  status: string;
  started_at: string;
  completed_at: string | null;
  agents_run: string[];
  total_latency_ms: number;
};

export type AgentEvent = {
  id: number;
  run_id: number;
  ticket_id: number;
  step_index: number;
  node_name: string;
  event_type: string;
  status: string;
  input_summary: string | null;
  output_summary: string | null;
  tool_name: string | null;
  citations: Citation[];
  latency_ms: number;
  created_at: string;
};

export type PendingAction = {
  id: number;
  ticket_id: number;
  action_type: string;
  payload_json: Record<string, unknown>;
  risk_level: string;
  status: string;
  created_at: string;
  decided_at: string | null;
  ticket_subject?: string | null;
  ticket_status?: string | null;
};

export type TicketWorkflowResponse = {
  ticket: Ticket;
  agent_run: AgentRun;
  agents_run: string[];
  events: AgentEvent[];
  pending_actions: PendingAction[];
  final_response: string | null;
  citations: Citation[];
};

export type TicketDetail = {
  ticket: Ticket;
  agent_run: AgentRun | null;
  events: AgentEvent[];
  pending_actions: PendingAction[];
};

export type KnowledgeDocument = {
  id: number;
  title: string;
  content: string;
  source: string;
  created_at: string;
};

export type StatsOverview = {
  total_tickets: number;
  resolved_tickets: number;
  escalated_tickets: number;
  pending_approval_count: number;
  average_latency: number;
  category_breakdown: Array<{ name: string; value: number }>;
  priority_breakdown: Array<{ name: string; value: number }>;
  escalation_rate: number;
  approval_rate: number;
  recent_runs: AgentRun[];
  latest_trace_preview: AgentEvent[];
};

export type EvalResult = {
  id: string;
  expected_route: string;
  actual_route: string;
  expected_category: string;
  actual_category: string;
  expected_priority: string;
  actual_priority: string;
  passed: boolean;
  latency_ms: number;
  llm_ok: boolean;
  llm_calls: LlmExecutionAudit;
  citation_ok: boolean;
  expected_citation: string | null;
  response_language_ok: boolean;
};

export type LlmExecutionAudit = {
  provider: string;
  model: string;
  attempted_calls: number;
  successful_calls: number;
  failed_calls: number;
  fallback_calls: number;
  retry_attempts: number;
};

export type EvalPayload = {
  locale: EvalLocale;
  run_id: string | null;
  started_at: string | null;
  completed_at: string | null;
  metrics: Record<string, number>;
  results: EvalResult[];
  failed_cases: EvalResult[];
  llm_execution: LlmExecutionAudit;
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<Record<string, string>>('/api/health'),
  stats: () => request<StatsOverview>('/api/stats/overview'),
  tickets: () => request<Ticket[]>('/api/tickets'),
  ticket: (id: number) => request<TicketDetail>(`/api/tickets/${id}`),
  createTicket: (payload: { subject: string; description: string; customer_email?: string }, deepSeekApiKey?: string | null) =>
    request<TicketWorkflowResponse>('/api/tickets', {
      method: 'POST',
      headers: deepSeekApiKey ? { 'X-DeepSeek-API-Key': deepSeekApiKey } : undefined,
      body: JSON.stringify(payload)
    }),
  approvals: () => request<PendingAction[]>('/api/approvals'),
  approve: (id: number) => request<{ action: PendingAction; ticket: Ticket }>(`/api/approvals/${id}/approve`, { method: 'POST' }),
  reject: (id: number) => request<{ action: PendingAction; ticket: Ticket }>(`/api/approvals/${id}/reject`, { method: 'POST' }),
  documents: () => request<KnowledgeDocument[]>('/api/rag/documents'),
  askRag: (question: string) =>
    request<{ answer: string; citations: Citation[] }>('/api/rag/ask', {
      method: 'POST',
      body: JSON.stringify({ question })
    }),
  reindex: () => request<{ indexed: number; documents: KnowledgeDocument[] }>('/api/rag/reindex', { method: 'POST' }),
  runEvals: (locale: EvalLocale, deepSeekApiKey?: string | null) =>
    request<EvalPayload>(`/api/evals/run?locale=${encodeURIComponent(locale)}`, {
      method: 'POST',
      headers: deepSeekApiKey ? { 'X-DeepSeek-API-Key': deepSeekApiKey } : undefined
    }),
  latestEvals: (locale: EvalLocale = 'en') =>
    request<EvalPayload>(`/api/evals/latest?locale=${encodeURIComponent(locale)}`)
};

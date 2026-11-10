import type { Experiment, ExperimentCreate, Run, RunCreate, WorkflowGraph } from './contracts';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  experiments: () => request<Experiment[]>('/experiments'),
  createExperiment: (payload: ExperimentCreate) => request<Experiment>('/experiments', { method: 'POST', body: JSON.stringify(payload) }),
  createRun: (id: string, payload: RunCreate) => request<Run>(`/experiments/${id}/runs`, { method: 'POST', body: JSON.stringify(payload) }),
  graph: () => request<WorkflowGraph>('/graph'),
};

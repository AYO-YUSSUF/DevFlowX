export type ExperimentStatus = 'active' | 'completed' | 'archived';
export type RunStatus = 'queued' | 'running' | 'succeeded' | 'failed';

export interface ModelVersion {
  id: string; experiment_id: string; run_id: string; name: string; version: number;
  created_at: string; metrics: Record<string, number>; parent_model_id: string | null;
}
export interface Run {
  id: string; experiment_id: string; status: RunStatus; created_at: string;
  parameters: Record<string, unknown>; metrics: Record<string, number>; notes: string;
  model_version: ModelVersion | null;
}
export interface Experiment {
  id: string; name: string; task: string; dataset: string; description: string;
  status: ExperimentStatus; created_at: string; updated_at: string;
  parameters: Record<string, unknown>; runs: Run[]; model_versions: ModelVersion[];
}
export interface GraphNode { id: string; kind: 'experiment' | 'run' | 'model'; label: string; detail: string }
export interface GraphEdge { source: string; target: string; relation: 'HAS_RUN' | 'PRODUCED' | 'PARENT_OF' }
export interface WorkflowGraph { nodes: GraphNode[]; edges: GraphEdge[] }
export interface ExperimentCreate {
  name: string; task: string; dataset: string; description: string; parameters: Record<string, unknown>;
}
export interface RunCreate {
  status: RunStatus; metrics: Record<string, number>; parameters: Record<string, unknown>;
  model_name?: string; notes: string;
}

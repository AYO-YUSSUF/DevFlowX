import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Bot,
  Boxes,
  ChevronDown,
  CircleHelp,
  Clock3,
  GitBranch,
  LayoutDashboard,
  Plus,
  Search,
  Settings2,
  Sparkles,
  X,
} from 'lucide-react';
import { api } from './api';
import type { Experiment, ExperimentCreate, WorkflowGraph } from './contracts';

const fmtDate = (value: string) =>
  new Date(value).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  });

function App() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [graph, setGraph] = useState<WorkflowGraph>({ nodes: [], edges: [] });
  const [selectedId, setSelectedId] = useState('');
  const [search, setSearch] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const refresh = useCallback(async () => {
    try {
      const [items, nextGraph] = await Promise.all([
        api.experiments(),
        api.graph(),
      ]);

      setExperiments(items);
      setGraph(nextGraph);
      setSelectedId((current) =>
        current && items.some((item) => item.id === current)
          ? current
          : items[0]?.id ?? '',
      );
      setError('');
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not reach the DevFlowX API',
      );
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const selected = experiments.find((item) => item.id === selectedId);
  const filtered = experiments.filter((experiment) =>
    `${experiment.name} ${experiment.task} ${experiment.dataset}`
      .toLowerCase()
      .includes(search.toLowerCase()),
  );
  const runs = selected?.runs ?? [];
  const newest = runs[0];
  const meanF1 = runs.length
    ? runs.reduce((sum, run) => sum + (run.metrics.f1 ?? 0), 0) / runs.length
    : 0;

  const nodes = useMemo(() => graph.nodes.slice(0, 9), [graph]);
  const graphPositions = useMemo(() => {
    const columns = { experiment: 0.12, run: 0.44, model: 0.76 } as const;
    const rowIndex: Record<string, number> = {};

    return new Map<string, { x: number; y: number }>(
      nodes.map((node) => {
        const row = rowIndex[node.kind] ?? 0;
        rowIndex[node.kind] = row + 1;

        return [node.id, {
          x: columns[node.kind] * 1000,
          y: 36 + (row % 2) * 76,
        }] as const;
      }),
    );
  }, [nodes]);

  async function createExperiment(payload: ExperimentCreate) {
    setBusy(true);
    try {
      const created = await api.createExperiment(payload);
      await refresh();
      setSelectedId(created.id);
      setShowCreate(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create experiment');
    } finally {
      setBusy(false);
    }
  }

  async function addDemoRun() {
    if (!selected) return;

    setBusy(true);
    try {
      await api.createRun(selected.id, {
        status: 'succeeded',
        parameters: { learning_rate: 0.001, epochs: 20 },
        metrics: { accuracy: 0.86, f1: 0.79 },
        model_name: 'churn-classifier',
        notes: 'Demo run. Replace these example metrics with actual training output.',
      });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create run');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Activity size={18} /></div>
          <div>
            <strong>devflow<span>x</span></strong>
            <small>ML WORKSPACE</small>
          </div>
        </div>

        <div className="workspace-switch">
          <div className="workspace-avatar">N</div>
          <div>
            <b>Northstar Labs</b>
            <small>Personal workspace</small>
          </div>
          <ChevronDown size={15} />
        </div>

        <div className="nav-label">WORKSPACE</div>
        <nav>
          <a className="nav-item active">
            <LayoutDashboard size={17} /> Overview
            <span className="nav-count">{experiments.length}</span>
          </a>
          <a className="nav-item">
            <Boxes size={17} /> Models
            <span className="nav-count">
              {experiments.reduce((count, experiment) => count + experiment.model_versions.length, 0)}
            </span>
          </a>
          <a className="nav-item"><GitBranch size={17} /> Version graph</a>
        </nav>

        <div className="sidebar-section">
          <div className="section-title">
            <span>EXPERIMENTS</span>
            <button
              className="icon-button"
              onClick={() => setShowCreate(true)}
              aria-label="Create experiment"
            >
              <Plus size={15} />
            </button>
          </div>

          <label className="search-box">
            <Search size={14} />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Find experiment..."
            />
          </label>

          <div className="experiment-nav">
            {filtered.map((experiment) => (
              <button
                key={experiment.id}
                className={`experiment-link ${selectedId === experiment.id ? 'selected' : ''}`}
                onClick={() => setSelectedId(experiment.id)}
              >
                <span className="status-dot" />
                <span className="experiment-link-text">{experiment.name}</span>
                <span className="run-count">{experiment.runs.length}</span>
              </button>
            ))}
            {!filtered.length && <p className="sidebar-empty">No matching experiments</p>}
          </div>
        </div>

        <div className="sidebar-bottom">
          <a className="nav-item"><Settings2 size={17} /> Settings</a>
          <a className="nav-item"><CircleHelp size={17} /> Help &amp; docs</a>
          <div className="user-card">
            <div className="user-avatar">JD</div>
            <div>
              <b>Jordan Davis</b>
              <small>ML Engineer</small>
            </div>
            <ChevronDown size={15} />
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumbs">
            <span>Workspace</span>
            <span className="crumb-slash">/</span>
            <b>{selected?.name ?? 'Overview'}</b>
          </div>
          <div className="top-actions">
            <span
              className={`connection ${error ? 'disconnected' : ''}`}
              title={error || 'The API is responding'}
              aria-live="polite"
            >
              <i /> {error ? 'API disconnected' : 'API connected'}
            </span>
            <button className="avatar-stack" title="Team workspace">
              <span>JD</span><span>AK</span><span>+3</span>
            </button>
            <button className="top-help" aria-label="Help">
              <CircleHelp size={17} />
            </button>
          </div>
        </header>

        <div className="content">
          {error && (
            <div className="error-banner" role="alert">
              <span>{error}</span>
              <button onClick={() => void refresh()}>Retry</button>
            </div>
          )}

          <div className="page-heading">
            <div>
              <div className="eyebrow">
                <span className="status-dot" /> EXPERIMENT WORKSPACE
                <span className="eyebrow-line" />
              </div>
              <h1>{selected?.name ?? 'Your ML workspace'}</h1>
              <p>
                {selected?.description || 'Track iterations, compare runs, and follow model lineage in one place.'}
              </p>
            </div>
            <div className="heading-actions">
              <button className="button secondary" onClick={addDemoRun} disabled={!selected || busy}>
                <Plus size={16} /> Log run
              </button>
              <button className="button primary" onClick={() => setShowCreate(true)} disabled={busy}>
                <Plus size={16} /> New experiment
              </button>
            </div>
          </div>

          <section className="stat-grid">
            <article className="stat-card">
              <div className="stat-head">
                <span>EXPERIMENTS</span>
                <span className="stat-icon"><Boxes size={16} /></span>
              </div>
              <div className="stat-value">{experiments.length.toString().padStart(2, '0')}</div>
              <div className="stat-foot">
                <span className="positive"><ArrowUpRight size={14} /> Active workspace</span>
                <span>Across all projects</span>
              </div>
            </article>

            <article className="stat-card">
              <div className="stat-head">
                <span>MODEL VERSIONS</span>
                <span className="stat-icon violet"><GitBranch size={16} /></span>
              </div>
              <div className="stat-value">
                {experiments.reduce((count, experiment) => count + experiment.model_versions.length, 0).toString().padStart(2, '0')}
              </div>
              <div className="stat-foot">
                <span className="neutral"><Activity size={13} /> {selected?.model_versions.length ?? 0} in selection</span>
                <span>Tracked lineage</span>
              </div>
            </article>

            <article className="stat-card">
              <div className="stat-head">
                <span>AVG. F1 SCORE</span>
                <span className="stat-icon amber"><Sparkles size={16} /></span>
              </div>
              <div className="stat-value">
                {meanF1 ? meanF1.toFixed(2) : '—'}
                <small>{meanF1 ? '/ 1.00' : ''}</small>
              </div>
              <div className="stat-foot">
                <span className="positive">
                  <ArrowUpRight size={14} /> Latest: {newest?.metrics.f1?.toFixed(2) ?? '—'}
                </span>
                <span>Recorded runs only</span>
              </div>
            </article>

            <article className="stat-card">
              <div className="stat-head">
                <span>LAST ACTIVITY</span>
                <span className="stat-icon blue"><Clock3 size={16} /></span>
              </div>
              <div className="stat-value date-value">{selected ? fmtDate(selected.updated_at) : '—'}</div>
              <div className="stat-foot">
                <span className="neutral"><ArrowDownRight size={13} /> {runs.length} recorded runs</span>
                <span>Recorded activity</span>
              </div>
            </article>
          </section>

          <div className="section-heading">
            <div>
              <h2>Experiment overview</h2>
              <p>Recent iterations and model lineage for the selected experiment.</p>
            </div>
            <button className="text-button" onClick={() => void refresh()}>
              Refresh data <ArrowUpRight size={14} />
            </button>
          </div>

          <section className="dashboard-grid">
            <article className="panel runs-panel">
              <div className="panel-heading">
                <div>
                  <h3>Recent runs</h3>
                  <p>Training history and evaluation metrics</p>
                </div>
                <button className="quiet-button">All runs <ArrowUpRight size={13} /></button>
              </div>

              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>RUN</th><th>STATUS</th><th>F1 SCORE</th><th>ACCURACY</th><th>PARAMETERS</th><th>DATE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.slice(0, 5).map((run) => (
                      <tr key={run.id}>
                        <td><span className="run-id"><i /> {run.id.slice(-8)}</span></td>
                        <td><span className={`pill ${run.status}`}>{run.status}</span></td>
                        <td className="metric-cell">{run.metrics.f1?.toFixed(2) ?? '—'}</td>
                        <td>{run.metrics.accuracy?.toFixed(2) ?? '—'}</td>
                        <td>
                          <span className="param-chip">
                            {Object.entries(run.parameters)
                              .slice(0, 2)
                              .map(([key, value]) => `${key}: ${value}`)
                              .join(' · ') || '—'}
                          </span>
                        </td>
                        <td className="date-cell">{fmtDate(run.created_at)}</td>
                      </tr>
                    ))}
                    {!runs.length && (
                      <tr>
                        <td colSpan={6} className="empty-state">
                          No runs yet. Log a run to start the experiment history.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="panel-footer">
                <span>Showing {Math.min(runs.length, 5)} of {runs.length} runs</span>
                <span><i className="legend-dot" /> Results are demo records until connected to training</span>
              </div>
            </article>

            <article className="panel lineage-panel">
              <div className="panel-heading">
                <div>
                  <h3>Model lineage</h3>
                  <p>Version history across experiments</p>
                </div>
                <button className="more-button" aria-label="More model lineage options">···</button>
              </div>

              <div className="lineage-wrap">
                <div className="lineage-rail" />
                {(selected?.model_versions ?? []).slice(-4).map((model, index) => (
                  <div className="lineage-item" key={model.id}>
                    <div className={`lineage-node ${index === (selected?.model_versions.length ?? 1) - 1 ? 'latest' : ''}`}>
                      <Boxes size={14} />
                    </div>
                    <div className="lineage-card">
                      <div className="lineage-top">
                        <b>{model.name}</b>
                        <span className="version-tag">v{model.version}</span>
                        {index === (selected?.model_versions.length ?? 1) - 1 && (
                          <span className="latest-tag">LATEST</span>
                        )}
                      </div>
                      <div className="lineage-metrics">
                        <span>F1 <b>{model.metrics.f1?.toFixed(2) ?? '—'}</b></span>
                        <span>ACC <b>{model.metrics.accuracy?.toFixed(2) ?? '—'}</b></span>
                        <span>{fmtDate(model.created_at)}</span>
                      </div>
                    </div>
                  </div>
                ))}
                {!selected?.model_versions.length && (
                  <div className="lineage-empty">
                    Model versions appear here when a run records a model name.
                  </div>
                )}
              </div>

              <div className="panel-footer">
                <span className="legend-line" />
                <span>Model version progression</span>
                <span className="graph-count"><GitBranch size={13} /> {graph.edges.length} relationships</span>
              </div>
            </article>
          </section>

          <section className="assistant-banner">
            <div className="assistant-icon"><Bot size={20} /><span /></div>
            <div className="assistant-copy">
              <div className="assistant-label"><Sparkles size={13} /> DEVFLOW ASSISTANT <span>PREVIEW</span></div>
              <b>Turn your next experiment into a faster iteration.</b>
              <p>AI code suggestions are being connected by the team. Generated code will require review before use.</p>
            </div>
            <button className="button assistant-button" disabled>
              <Sparkles size={15} /> Assistant coming soon
            </button>
            <div className="assistant-orbit orbit-one" />
            <div className="assistant-orbit orbit-two" />
          </section>

          <section className="graph-strip">
            <div className="graph-strip-head">
              <div>
                <div className="graph-eyebrow"><GitBranch size={14} /> WORKFLOW GRAPH</div>
                <h2>Follow every experiment change</h2>
                <p>Relationships across experiment, run, and model version records.</p>
              </div>
              <span className="local-badge"><i /> WORKFLOW GRAPH</span>
            </div>

            <div className="graph-canvas">
              <div className="graph-grid-bg" />
              {nodes.map((node) => {
                const position = graphPositions.get(node.id);
                if (!position) return null;

                return (
                  <div
                    className={`graph-node node-${node.kind}`}
                    key={node.id}
                    style={{ left: `${position.x / 10}%`, top: `${position.y - 13}px` }}
                  >
                    <div className="graph-node-icon">
                      {node.kind === 'experiment' ? <Activity size={14} /> : <Boxes size={14} />}
                    </div>
                    <div>
                      <b>{node.label}</b>
                      <small>{node.kind} · {node.detail}</small>
                    </div>
                  </div>
                );
              })}
              <svg
                className="graph-lines"
                viewBox="0 0 1000 150"
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                {graph.edges.map((edge) => {
                  const from = graphPositions.get(edge.source);
                  const to = graphPositions.get(edge.target);
                  if (!from || !to) return null;

                  return (
                    <path
                      key={`${edge.source}-${edge.target}-${edge.relation}`}
                      d={`M${from.x + 160} ${from.y} C${from.x + 210} ${from.y} ${to.x - 20} ${to.y} ${to.x - 6} ${to.y}`}
                    />
                  );
                })}
              </svg>
              {!nodes.length && (
                <div className="graph-empty">Create an experiment to build its workflow graph.</div>
              )}
            </div>

            <div className="graph-footer">
              <span><i className="key-dot exp-key" /> Experiment</span>
              <span><i className="key-dot model-key" /> Model version</span>
              <span><i className="key-dot run-key" /> Run</span>
              <span className="graph-footer-count">
                {graph.nodes.length} nodes <b>·</b> {graph.edges.length} edges
              </span>
            </div>
          </section>

          <footer className="page-footer">
            <span>DEVFLOWX <b>·</b> ML DEVELOPMENT WORKSPACE</span>
            <span>
              Prototype build <b>0.1.0</b> <i />
              {error ? 'API connection issue' : 'API connected'}
            </span>
          </footer>
        </div>
      </main>

      {showCreate && (
        <CreateExperimentModal
          busy={busy}
          onClose={() => setShowCreate(false)}
          onSubmit={createExperiment}
        />
      )}
    </div>
  );
}

function CreateExperimentModal({
  busy,
  onClose,
  onSubmit,
}: {
  busy: boolean;
  onClose: () => void;
  onSubmit: (value: ExperimentCreate) => void;
}) {
  const [name, setName] = useState('');
  const [task, setTask] = useState('Binary classification');
  const [dataset, setDataset] = useState('');
  const [description, setDescription] = useState('');

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => event.target === event.currentTarget && onClose()}
    >
      <form
        className="modal"
        onSubmit={(event) => {
          event.preventDefault();
          void onSubmit({ name, task, dataset, description, parameters: {} });
        }}
      >
        <div className="modal-head">
          <div>
            <span className="eyebrow">NEW WORKSPACE ITEM</span>
            <h2>Create experiment</h2>
          </div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <label>
          Experiment name
          <input
            required
            maxLength={120}
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="e.g. Churn model v2"
          />
        </label>
        <label>
          ML task
          <input required maxLength={160} value={task} onChange={(event) => setTask(event.target.value)} />
        </label>
        <label>
          Dataset reference
          <input
            required
            maxLength={240}
            value={dataset}
            onChange={(event) => setDataset(event.target.value)}
            placeholder="Dataset name or URI"
          />
        </label>
        <label>
          Description
          <textarea
            maxLength={1000}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="What are you trying to learn?"
          />
        </label>

        <div className="modal-actions">
          <button type="button" className="button secondary" onClick={onClose}>Cancel</button>
          <button className="button primary" disabled={busy}>
            <Plus size={15} /> Create experiment
          </button>
        </div>
      </form>
    </div>
  );
}

export default App;

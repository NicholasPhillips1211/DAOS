import { ChangeEvent, useEffect, useMemo, useState } from 'react';
import { listWorkspaceDatasets, runDatasetSql, uploadDatasetFile } from './features/ingestion/api';
import { getWorkspaceSummary } from './features/workspace/api';
import { DashboardDraftPreview, DatasetRecord, IngestionUploadRead, QueryResult, WorkspaceSummaryRead } from './types/domain';
import { WorkflowState } from './WorkflowState';

type IngestionWizardProps = {
  apiBase: string;
  workspaceId: number;
  userEmail: string;
  onPrepareDashboard?: (datasetName: string) => void;
  onStatusChange?: (message: string) => void;
  onPreviewDashboardFromQuery?: (payload: {
    datasetName: string;
    datasetId: number;
    columns: string[];
    rowCount: number;
  }) => Promise<DashboardDraftPreview>;
  onCreateDashboardFromQuery?: (payload: {
    datasetName: string;
    datasetId: number;
    columns: string[];
    rowCount: number;
    approvedDraft?: DashboardDraftPreview;
  }) => Promise<void> | void;
};

type PreviewSummary = {
  headers: string[];
  sampleRows: string[][];
};

type WizardStage = 'choose' | 'preview' | 'upload' | 'query' | 'dashboard';

type WizardStageConfig = {
  id: WizardStage;
  label: string;
  detail: string;
};

const wizardStages: WizardStageConfig[] = [
  { id: 'choose', label: 'Choose source', detail: 'Pick a CSV and name the dataset.' },
  { id: 'preview', label: 'Preview schema', detail: 'Check headers and sample rows before upload.' },
  { id: 'upload', label: 'Upload and profile', detail: 'Persist the file and generate quality metrics.' },
  { id: 'query', label: 'Run analysis', detail: 'Use the suggested SQL against the virtual table.' },
  { id: 'dashboard', label: 'Prepare delivery', detail: 'Turn the query result into a dashboard draft.' },
];

const panelClass = 'rounded-[1.75rem] border border-white/10 bg-slate-950/65 p-5 shadow-[0_24px_90px_rgba(0,0,0,0.25)] backdrop-blur';
const inputClass =
  'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-cyan-300/60 focus:bg-white/8';

function parseCsvPreview(text: string, limit = 5): PreviewSummary {
  const lines = text
    .replace(/^\uFEFF/, '')
    .split(/\r?\n/)
    .map((line) => line.trimEnd())
    .filter((line) => line.length > 0);

  if (lines.length === 0) {
    return { headers: [], sampleRows: [] };
  }

  const rows = lines.map((line) =>
    line
      .split(',')
      .map((value) => value.trim())
      .map((value) => value.replace(/^"|"$/g, '')),
  );

  const headers = rows[0] ?? [];
  return {
    headers,
    sampleRows: rows.slice(1, limit + 1),
  };
}

function buildSuggestedSql(datasetName: string, headers: string[]): string {
  const title = datasetName.trim() || 'uploaded dataset';
  const selectedColumns = headers.slice(0, 5).map((header) => `"${header}"`).join(', ');

  return headers.length > 0
    ? `-- ${title}
SELECT ${selectedColumns}
FROM dataset
ORDER BY 1 DESC
LIMIT 25;`
    : `-- ${title}
SELECT *
FROM dataset
LIMIT 25;`;
}

export function IngestionWizard({
  apiBase,
  workspaceId,
  userEmail,
  onPrepareDashboard,
  onStatusChange,
  onPreviewDashboardFromQuery,
  onCreateDashboardFromQuery,
}: IngestionWizardProps) {
  const [datasetName, setDatasetName] = useState('Quarterly Sales Upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<PreviewSummary>({ headers: [], sampleRows: [] });
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<IngestionUploadRead | null>(null);
  const [datasets, setDatasets] = useState<DatasetRecord[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('');
  const [querySql, setQuerySql] = useState('');
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [draftPreviewLoading, setDraftPreviewLoading] = useState(false);
  const [dashboardDraftPreview, setDashboardDraftPreview] = useState<DashboardDraftPreview | null>(null);
  const [approvalChecked, setApprovalChecked] = useState(false);
  const [dashboardCreatingFromQuery, setDashboardCreatingFromQuery] = useState(false);
  const [workspaceSummary, setWorkspaceSummary] = useState<WorkspaceSummaryRead | null>(null);
  const [loadingWorkspaceSummary, setLoadingWorkspaceSummary] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [loadingDatasets, setLoadingDatasets] = useState(false);

  const queryTemplate = useMemo(() => buildSuggestedSql(datasetName, preview.headers), [datasetName, preview.headers]);
  const canUpload = Boolean(selectedFile && datasetName.trim());
  const activeDatasetId = selectedDatasetId ? Number(selectedDatasetId) : null;
  // The wizard now exposes the user's current place in the ingestion-to-insight path.
  const currentStage: WizardStage = dashboardDraftPreview
    ? 'dashboard'
    : queryResult
      ? 'query'
      : uploadResult
        ? 'upload'
        : preview.headers.length > 0
          ? 'preview'
          : 'choose';
  const currentStageIndex = wizardStages.findIndex((stage) => stage.id === currentStage);
  const progressPercent = ((currentStageIndex + 1) / wizardStages.length) * 100;
  const nextStage = wizardStages[Math.min(currentStageIndex + 1, wizardStages.length - 1)];

  useEffect(() => {
    setQuerySql(queryTemplate);
  }, [queryTemplate]);

  useEffect(() => {
    let cancelled = false;

    async function loadWorkspaceSummary(): Promise<void> {
      setLoadingWorkspaceSummary(true);
      try {
        const summary = await getWorkspaceSummary(apiBase, userEmail, workspaceId);
        if (!cancelled) {
          setWorkspaceSummary(summary);
        }
      } catch {
        if (!cancelled) {
          setWorkspaceSummary(null);
        }
      } finally {
        if (!cancelled) {
          setLoadingWorkspaceSummary(false);
        }
      }
    }

    void loadWorkspaceSummary();

    return () => {
      cancelled = true;
    };
  }, [apiBase, userEmail, workspaceId]);

  useEffect(() => {
    let cancelled = false;

    // This effect isolates dataset discovery so workspace switches refresh options without touching upload/query logic.
    async function loadDatasets(): Promise<void> {
      setLoadingDatasets(true);
      try {
        const items = await listWorkspaceDatasets(apiBase, userEmail, workspaceId);
        if (!cancelled) {
          setDatasets(items);
          if (items.length > 0) {
            setSelectedDatasetId(String(items[0].id));
          }
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : 'Failed to load datasets');
        }
      } finally {
        if (!cancelled) {
          setLoadingDatasets(false);
        }
      }
    }

    void loadDatasets();

    return () => {
      cancelled = true;
    };
  }, [apiBase, workspaceId]);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>): Promise<void> {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setUploadResult(null);
    setError(null);
    setSuccessMessage(null);

    if (!file) {
      setPreview({ headers: [], sampleRows: [] });
      return;
    }

    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('Only CSV files are supported for the ingestion wizard.');
      setPreview({ headers: [], sampleRows: [] });
      return;
    }

    const text = await file.text();
    setPreview(parseCsvPreview(text));
    if (!datasetName.trim()) {
      setDatasetName(file.name.replace(/\.csv$/i, '').replace(/[-_]+/g, ' '));
    }
  }

  // Upload orchestration is intentionally linear so state transitions are explicit for the guided workflow.
  async function handleUpload(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!selectedFile) {
      setError('Choose a CSV file before uploading.');
      return;
    }
    if (!datasetName.trim()) {
      setError('Give the dataset a name before uploading.');
      return;
    }

    setError(null);
  setSuccessMessage(null);
    setUploading(true);

    try {
      const result = await uploadDatasetFile(apiBase, userEmail, {
        workspaceId,
        datasetName: datasetName.trim(),
        file: selectedFile,
      });
      setUploadResult(result);
      setSelectedDatasetId(String(result.dataset_id));
      setDatasets((previous) => [
        {
          id: result.dataset_id,
          workspace_id: result.workspace_id,
          name: result.dataset_name,
          source_type: 'file',
          state: result.state,
          storage_path: result.storage_path,
          created_at: result.created_at,
        },
        ...previous.filter((dataset) => dataset.id !== result.dataset_id),
      ].slice(0, 4));
      void getWorkspaceSummary(apiBase, userEmail, workspaceId).then(setWorkspaceSummary).catch(() => undefined);
      onPrepareDashboard?.(result.dataset_name);
      onStatusChange?.(`Dataset uploaded: ${result.dataset_name}`);
      setSuccessMessage(`Uploaded ${result.dataset_name} and generated profile results.`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Failed to upload dataset');
    } finally {
      setUploading(false);
    }
  }

  // Queries run against the server-side virtual table to guarantee parity with backend SQL semantics.
  async function runQuery(): Promise<void> {
    if (!activeDatasetId) {
      setError('Select a dataset before running a query.');
      return;
    }
    if (!querySql.trim()) {
      setError('Query text is required.');
      return;
    }

    setError(null);
  setSuccessMessage(null);
    setQueryLoading(true);

    try {
      const result = await runDatasetSql(apiBase, userEmail, {
        datasetId: activeDatasetId,
        sql: querySql,
      });
      setQueryResult(result);
      setDashboardDraftPreview(null);
      setApprovalChecked(false);
      onStatusChange?.(`Query completed with ${result.row_count} row${result.row_count === 1 ? '' : 's'}`);
      setSuccessMessage(`Query completed with ${result.row_count} row${result.row_count === 1 ? '' : 's'} returned.`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Failed to run query');
    } finally {
      setQueryLoading(false);
    }
  }

  // Draft preview is separate from create so analysts can review/reword generated metadata before persistence.
  async function previewDashboardDraft(): Promise<void> {
    if (!queryResult || !activeDatasetId) {
      setError('Run a query first to preview a dashboard draft.');
      return;
    }
    if (!onPreviewDashboardFromQuery) {
      setError('Dashboard preview callback is not configured.');
      return;
    }

    const selectedDataset = datasets.find((dataset) => dataset.id === activeDatasetId);
    const resolvedDatasetName = selectedDataset?.name ?? uploadResult?.dataset_name ?? datasetName;

    setError(null);
    setSuccessMessage(null);
    setDraftPreviewLoading(true);
    try {
      const preview = await onPreviewDashboardFromQuery({
        datasetName: resolvedDatasetName,
        datasetId: activeDatasetId,
        columns: queryResult.columns,
        rowCount: queryResult.row_count,
      });
      setDashboardDraftPreview(preview);
      setApprovalChecked(false);
      onStatusChange?.('Dashboard draft preview ready for verification.');
      setSuccessMessage('Dashboard draft preview is ready for review.');
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Failed to preview dashboard draft');
    } finally {
      setDraftPreviewLoading(false);
    }
  }

  function updateDashboardDraftPreview(patch: Partial<DashboardDraftPreview>): void {
    setDashboardDraftPreview((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        ...patch,
      };
    });
    setApprovalChecked(false);
  }

  // Creation enforces an approval gate to reduce accidental dashboard churn from exploratory queries.
  async function createDashboardFromQuery(): Promise<void> {
    if (!queryResult || !activeDatasetId) {
      setError('Run a query first to create a dashboard from its result.');
      return;
    }
    if (!dashboardDraftPreview) {
      setError('Generate and verify a dashboard draft preview before approval.');
      return;
    }
    if (!approvalChecked) {
      setError('Confirm draft verification before approving dashboard creation.');
      return;
    }
    if (!onCreateDashboardFromQuery) {
      setError('Dashboard creation callback is not configured.');
      return;
    }

    const selectedDataset = datasets.find((dataset) => dataset.id === activeDatasetId);
    const resolvedDatasetName = selectedDataset?.name ?? uploadResult?.dataset_name ?? datasetName;

    setError(null);
    setSuccessMessage(null);
    setDashboardCreatingFromQuery(true);
    try {
      await Promise.resolve(
        onCreateDashboardFromQuery({
          datasetName: resolvedDatasetName,
          datasetId: activeDatasetId,
          columns: queryResult.columns,
          rowCount: queryResult.row_count,
          approvedDraft: dashboardDraftPreview,
        }),
      );
      onStatusChange?.(`Dashboard created from query result for ${resolvedDatasetName}`);
      setSuccessMessage(`Dashboard created from query result for ${resolvedDatasetName}.`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Failed to create dashboard from query');
    } finally {
      setDashboardCreatingFromQuery(false);
    }
  }

  return (
    <section className={panelClass}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-cyan-200/90">Ingestion Wizard</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">Upload a CSV and preview the path to insight</h2>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-300">
            Step through upload, schema preview, and a suggested SQL query before you hand the dataset off to dashboards or automation.
          </p>
        </div>
        <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300">
          {loadingWorkspaceSummary
            ? 'Loading workspace summary...'
            : workspaceSummary
              ? `${workspaceSummary.dataset_count} dataset${workspaceSummary.dataset_count === 1 ? '' : 's'} in workspace`
              : loadingDatasets
                ? 'Loading recent datasets...'
                : `${datasets.length} recent dataset${datasets.length === 1 ? '' : 's'}`}
        </div>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        {/* Surface a single success state so completed steps are visible, not just implied by empty states. */}
        {successMessage ? (
          <div className="xl:col-span-2">
            <WorkflowState variant="success" title="Step complete" description={successMessage} />
          </div>
        ) : null}

        <form className="space-y-5" onSubmit={handleUpload}>
          {/* The stage strip keeps the ingestion wizard oriented around the next concrete action. */}
          <div className="rounded-2xl border border-cyan-300/20 bg-cyan-400/10 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.25em] text-cyan-100">Workflow progress</p>
                <p className="mt-1 text-sm text-slate-100">
                  You are on <span className="font-semibold text-white">{wizardStages[currentStageIndex]?.label}</span>.
                </p>
              </div>
              <div className="rounded-full border border-white/10 bg-slate-950/60 px-3 py-1 text-xs text-slate-300">
                Next: {nextStage.label}
              </div>
            </div>
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-950/70">
              <div className="h-full rounded-full bg-gradient-to-r from-cyan-300 to-emerald-300" style={{ width: `${progressPercent}%` }} />
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
              {wizardStages.map((stage, index) => {
                const isActive = stage.id === currentStage;
                const isComplete = index < currentStageIndex;

                return (
                  <div
                    key={stage.id}
                    className={`rounded-xl border p-3 ${
                      isActive
                        ? 'border-cyan-300/40 bg-cyan-400/15 text-white'
                        : isComplete
                          ? 'border-emerald-300/20 bg-emerald-400/10 text-emerald-50'
                          : 'border-white/10 bg-slate-950/50 text-slate-300'
                    }`}
                  >
                    <p className="text-[11px] uppercase tracking-[0.25em]">{stage.label}</p>
                    <p className="mt-2 text-xs leading-5 text-inherit/90">{stage.detail}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {workspaceSummary ? (
            workspaceSummary.has_datasets ? (
              <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Workspace summary</p>
                    <p className="mt-1 text-sm text-slate-100">{workspaceSummary.workspace_name}</p>
                  </div>
                  <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
                    {workspaceSummary.membership_count} member{workspaceSummary.membership_count === 1 ? '' : 's'}
                  </div>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-300">{workspaceSummary.recommended_next_action}</p>
                {workspaceSummary.recent_datasets.length > 0 ? (
                  <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                    {workspaceSummary.recent_datasets.map((dataset) => (
                      <div key={dataset.id} className="rounded-xl border border-white/10 bg-white/5 p-3">
                        <p className="text-sm font-semibold text-white">{dataset.name}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-400">{dataset.source_type}</p>
                        <p className="mt-2 text-xs text-slate-400">State: {dataset.state}</p>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : (
              <WorkflowState
                variant="empty"
                title="No datasets yet"
                description={workspaceSummary.recommended_next_action}
              />
            )
          ) : null}

          <div className="grid gap-4 md:grid-cols-[1fr_1.2fr]">
            <label className="space-y-2">
              <span className="text-xs uppercase tracking-[0.25em] text-slate-400">Dataset name</span>
              <input
                value={datasetName}
                onChange={(event) => setDatasetName(event.target.value)}
                className={inputClass}
                placeholder="Quarterly Sales Upload"
              />
            </label>
            <label className="space-y-2">
              <span className="text-xs uppercase tracking-[0.25em] text-slate-400">CSV file</span>
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={handleFileChange}
                className="block w-full cursor-pointer rounded-2xl border border-dashed border-white/15 bg-white/5 px-4 py-3 text-sm text-slate-300 file:mr-4 file:rounded-full file:border-0 file:bg-cyan-400 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-slate-950 hover:border-cyan-300/40"
              />
            </label>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {[
              { step: '1', title: 'Choose source', body: selectedFile ? selectedFile.name : 'CSV upload is the current MVP path.' },
              { step: '2', title: 'Preview schema', body: preview.headers.length > 0 ? `${preview.headers.length} columns detected.` : 'No preview yet.' },
              { step: '3', title: 'Upload and profile', body: 'The backend stores the file, profiles it, and returns quality metrics.' },
            ].map((item) => (
              <div key={item.step} className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-cyan-400 text-sm font-bold text-slate-950">
                    {item.step}
                  </div>
                  <h3 className="text-sm font-semibold text-white">{item.title}</h3>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-400">{item.body}</p>
              </div>
            ))}
          </div>

          {preview.headers.length > 0 ? (
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="flex items-center justify-between gap-3">
                <h3 className="text-sm uppercase tracking-[0.25em] text-slate-300">Schema preview</h3>
                <span className="rounded-full border border-white/10 bg-slate-950/60 px-3 py-1 text-xs text-slate-300">
                  {preview.headers.length} columns
                </span>
              </div>
              <div className="mt-4 overflow-hidden rounded-xl border border-white/10">
                <table className="w-full border-collapse text-left text-sm text-slate-200">
                  <thead className="bg-slate-950/70 text-xs uppercase tracking-[0.2em] text-slate-400">
                    <tr>
                      {preview.headers.map((header) => (
                        <th key={header} className="px-3 py-2 font-medium">
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.sampleRows.length > 0 ? (
                      preview.sampleRows.map((row, rowIndex) => (
                        <tr key={`${rowIndex}-${row.join('-')}`} className={rowIndex % 2 === 0 ? 'bg-white/5' : 'bg-transparent'}>
                          {preview.headers.map((_, columnIndex) => (
                            <td key={`${rowIndex}-${columnIndex}`} className="px-3 py-2 text-slate-300">
                              {row[columnIndex] ?? '—'}
                            </td>
                          ))}
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td className="px-3 py-4 text-slate-400" colSpan={preview.headers.length}>
                          The file has headers but no data rows to preview.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            // The empty preview state now explains the next action instead of leaving the panel blank.
            <WorkflowState
              variant="empty"
              title="Preview the file first"
              description="Choose a CSV to generate a schema preview and sample rows before uploading the dataset."
            />
          )}

          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm uppercase tracking-[0.25em] text-slate-300">Query builder</h3>
              <span className="rounded-full border border-white/10 bg-slate-950/60 px-3 py-1 text-xs text-slate-300">Suggested starting point</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              Use the detected columns to move straight into analysis. This template can be pasted into the lakehouse query endpoint or adapted for a dashboard metric.
            </p>
            <textarea
              value={querySql}
              onChange={(event) => setQuerySql(event.target.value)}
              className="mt-4 min-h-36 w-full resize-y rounded-xl border border-white/10 bg-slate-950/70 p-4 font-mono text-xs leading-6 text-cyan-100 outline-none focus:border-cyan-300/50"
            />
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => setQuerySql(queryTemplate)}
                className="rounded-full border border-white/20 bg-white/5 px-4 py-2 text-xs font-semibold text-slate-200 transition hover:border-cyan-300/50"
              >
                Reset to template
              </button>
              <span className="text-xs text-slate-400">The query endpoint reads from a virtual table named dataset.</span>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={!canUpload || uploading}
              className="rounded-full bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {uploading ? 'Uploading and profiling...' : 'Upload and profile dataset'}
            </button>
            <span className="self-center text-sm text-slate-400">
              Uploads are stored locally and profiled automatically by the backend.
            </span>
          </div>
        </form>

        <div className="space-y-6">
          <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm uppercase tracking-[0.25em] text-slate-300">Recent datasets</h3>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">Workspace #{workspaceId}</span>
            </div>
            <label className="mt-4 block space-y-2">
              <span className="text-xs uppercase tracking-[0.2em] text-slate-400">Dataset for query runner</span>
              <select
                value={selectedDatasetId}
                onChange={(event) => setSelectedDatasetId(event.target.value)}
                className={inputClass}
              >
                <option value="">Select dataset</option>
                {datasets.map((dataset) => (
                  <option key={dataset.id} value={dataset.id}>
                    {dataset.name} (ID {dataset.id})
                  </option>
                ))}
              </select>
            </label>
            <div className="mt-4 space-y-3">
              {loadingDatasets ? (
                <WorkflowState
                  variant="loading"
                  title="Loading datasets"
                  description="Fetching recent workspace datasets so you can choose one for query and dashboard creation."
                />
              ) : datasets.length === 0 ? (
                // The empty dataset list now points the user toward the same guided flow used elsewhere.
                <WorkflowState
                  variant="empty"
                  title="No datasets yet"
                  description="Upload the first CSV to begin the flow and make the query runner available."
                  action={
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
                      After upload, the next step is {nextStage.label.toLowerCase()}.
                    </p>
                  }
                />
              ) : (
                datasets.map((dataset) => (
                  <div key={dataset.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium text-white">{dataset.name}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-400">
                          {dataset.source_type} · {dataset.state}
                        </p>
                      </div>
                      <span className="rounded-full border border-cyan-300/20 bg-cyan-400/10 px-3 py-1 text-xs text-cyan-100">
                        ID {dataset.id}
                      </span>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-slate-400">
                      {dataset.storage_path ?? 'No storage path recorded.'}
                    </p>
                  </div>
                ))
              )}
            </div>
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={runQuery}
                disabled={!activeDatasetId || queryLoading}
                className="rounded-full bg-emerald-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {queryLoading ? 'Running query...' : 'Run query now'}
              </button>
              <button
                type="button"
                onClick={() => onPrepareDashboard?.(datasetName)}
                className="rounded-full border border-white/20 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-cyan-300/50"
              >
                Use for dashboard
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm uppercase tracking-[0.25em] text-slate-300">Upload result</h3>
              <span className="rounded-full border border-white/10 bg-slate-950/60 px-3 py-1 text-xs text-slate-300">
                {uploadResult ? 'Ready for analysis' : 'Waiting for upload'}
              </span>
            </div>
            {uploadResult ? (
              <div className="mt-4 space-y-3 text-sm text-slate-200">
                <div className="rounded-xl border border-emerald-300/20 bg-emerald-400/10 p-3">
                  <p className="font-medium text-emerald-100">{uploadResult.dataset_name} uploaded successfully</p>
                  <p className="mt-1 text-emerald-50/80">Quality score: {uploadResult.quality_score}% · {uploadResult.row_count} rows · {uploadResult.rejected_rows} rejected</p>
                </div>
                <div className="rounded-xl border border-white/10 bg-slate-950/60 p-3 text-slate-300">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Next move</p>
                  <p className="mt-2 leading-6">Use the query template above, then create a dashboard from the uploaded dataset or feed it into the automation planner.</p>
                </div>
              </div>
            ) : (
              // The upload placeholder now carries the current stage so the user understands what the wizard is waiting on.
              <div className="mt-4">
                <WorkflowState
                  variant="info"
                  title="Waiting for an upload"
                  description="Upload a CSV to see row counts, quality score, and storage details here."
                  action={
                    <p className="text-xs uppercase tracking-[0.2em] text-amber-50/80">
                      Current stage: {wizardStages[currentStageIndex]?.label}
                    </p>
                  }
                />
              </div>
            )}
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm uppercase tracking-[0.25em] text-slate-300">Query result</h3>
              <span className="rounded-full border border-white/10 bg-slate-950/60 px-3 py-1 text-xs text-slate-300">
                {queryResult ? `${queryResult.row_count} row${queryResult.row_count === 1 ? '' : 's'}` : 'No query run'}
              </span>
            </div>
            {queryResult ? (
              <div className="mt-4 space-y-4">
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={previewDashboardDraft}
                    disabled={draftPreviewLoading}
                    className="rounded-full bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {draftPreviewLoading ? 'Building draft preview...' : 'Preview dashboard draft'}
                  </button>
                  <span className="text-xs text-slate-400">Generates a recommended chart-backed draft that must be verified before approval.</span>
                </div>

                {dashboardDraftPreview ? (
                  <div className="rounded-xl border border-cyan-300/20 bg-cyan-400/10 p-4 text-sm text-slate-100">
                    <p className="text-xs uppercase tracking-[0.2em] text-cyan-100">Draft preview</p>
                    <div className="mt-3 space-y-3">
                      <label className="block space-y-2">
                        <span className="text-xs uppercase tracking-[0.2em] text-slate-300">Dashboard title</span>
                        <input
                          value={dashboardDraftPreview.name}
                          onChange={(event) => updateDashboardDraftPreview({ name: event.target.value })}
                          className={inputClass}
                        />
                      </label>
                      <label className="block space-y-2">
                        <span className="text-xs uppercase tracking-[0.2em] text-slate-300">Dashboard description</span>
                        <textarea
                          value={dashboardDraftPreview.description}
                          onChange={(event) => updateDashboardDraftPreview({ description: event.target.value })}
                          className={`${inputClass} min-h-24 resize-y`}
                        />
                      </label>
                    </div>
                    {dashboardDraftPreview.recommendation ? (
                      <div className="mt-3 rounded-lg border border-white/15 bg-slate-950/50 p-3">
                        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Chart recommendation</p>
                        <p className="mt-1 text-sm font-medium text-white">{dashboardDraftPreview.recommendation.chartType}</p>
                        <p className="mt-1 text-sm text-slate-300">{dashboardDraftPreview.recommendation.reason}</p>
                        {dashboardDraftPreview.recommendation.bestPractices.length > 0 ? (
                          <ul className="mt-3 space-y-2 text-sm text-slate-300">
                            {dashboardDraftPreview.recommendation.bestPractices.map((practice) => (
                              <li key={practice} className="rounded-md border border-white/10 bg-white/5 px-3 py-2">
                                {practice}
                              </li>
                            ))}
                          </ul>
                        ) : null}
                      </div>
                    ) : null}

                    <label className="mt-4 flex items-start gap-2 text-sm text-slate-200">
                      <input
                        type="checkbox"
                        checked={approvalChecked}
                        onChange={(event) => setApprovalChecked(event.target.checked)}
                        className="mt-1 h-4 w-4 rounded border-white/20 bg-slate-950/70"
                      />
                      I verified this draft preview and approve dashboard creation.
                    </label>

                    <button
                      type="button"
                      onClick={createDashboardFromQuery}
                      disabled={dashboardCreatingFromQuery || !approvalChecked}
                      className="mt-4 rounded-full bg-emerald-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {dashboardCreatingFromQuery ? 'Creating dashboard...' : 'Approve and create dashboard'}
                    </button>
                  </div>
                ) : null}

                <div className="overflow-auto rounded-xl border border-white/10">
                  <table className="w-full border-collapse text-left text-sm text-slate-200">
                    <thead className="bg-slate-950/70 text-xs uppercase tracking-[0.2em] text-slate-400">
                      <tr>
                        {queryResult.columns.map((column) => (
                          <th key={column} className="px-3 py-2 font-medium">
                            {column}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {queryResult.rows.slice(0, 10).map((row, rowIndex) => (
                        <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white/5' : 'bg-transparent'}>
                          {queryResult.columns.map((column) => (
                            <td key={`${rowIndex}-${column}`} className="px-3 py-2 text-slate-300">
                              {String(row[column] ?? '—')}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              // The empty query state now makes the next query action obvious and ties it back to the guided flow.
              <div className="mt-4">
                <WorkflowState
                  variant="empty"
                  title="No query result yet"
                  description="Select a dataset, tune the SQL in Query builder, then run the query to preview rows here."
                  action={
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
                      The next action is {queryResult ? 'preview dashboard draft' : 'run the query'}.
                    </p>
                  }
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {error ? (
        <div className="mt-4">
          <WorkflowState variant="error" title="Workflow error" description={error} />
        </div>
      ) : null}
    </section>
  );
}

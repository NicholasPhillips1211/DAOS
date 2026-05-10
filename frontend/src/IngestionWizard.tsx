import { ChangeEvent, useEffect, useMemo, useState } from 'react';

type DatasetRecord = {
  id: number;
  workspace_id: number;
  name: string;
  source_type: string;
  state: string;
  storage_path?: string | null;
  created_at: string;
};

type IngestionUploadRead = {
  dataset_id: number;
  workspace_id: number;
  dataset_name: string;
  state: string;
  quality_score: number;
  row_count: number;
  rejected_rows: number;
  storage_path: string;
  report_id: number;
  created_at: string;
};

type IngestionWizardProps = {
  apiBase: string;
  workspaceId: number;
  onPrepareDashboard?: (datasetName: string) => void;
  onStatusChange?: (message: string) => void;
};

type PreviewSummary = {
  headers: string[];
  sampleRows: string[][];
};

type QueryResult = {
  columns: string[];
  rows: Array<Record<string, unknown>>;
  row_count: number;
};

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

export function IngestionWizard({ apiBase, workspaceId, onPrepareDashboard, onStatusChange }: IngestionWizardProps) {
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
  const [error, setError] = useState<string | null>(null);
  const [loadingDatasets, setLoadingDatasets] = useState(false);

  const queryTemplate = useMemo(() => buildSuggestedSql(datasetName, preview.headers), [datasetName, preview.headers]);
  const canUpload = Boolean(selectedFile && datasetName.trim());
  const activeDatasetId = selectedDatasetId ? Number(selectedDatasetId) : null;

  useEffect(() => {
    setQuerySql(queryTemplate);
  }, [queryTemplate]);

  useEffect(() => {
    let cancelled = false;

    async function loadDatasets(): Promise<void> {
      setLoadingDatasets(true);
      try {
        const response = await fetch(`${apiBase}/datasets`);
        if (!response.ok) {
          throw new Error(`Dataset list failed (${response.status})`);
        }
        const items = (await response.json()) as DatasetRecord[];
        if (!cancelled) {
          const scoped = items.filter((item) => item.workspace_id === workspaceId).slice(0, 4);
          setDatasets(scoped);
          if (scoped.length > 0) {
            setSelectedDatasetId(String(scoped[0].id));
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
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('workspace_id', String(workspaceId));
      formData.append('dataset_name', datasetName.trim());
      formData.append('file', selectedFile);

      const response = await fetch(`${apiBase}/ingestion/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed (${response.status})`);
      }

      const result = (await response.json()) as IngestionUploadRead;
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
      onPrepareDashboard?.(result.dataset_name);
      onStatusChange?.(`Dataset uploaded: ${result.dataset_name}`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Failed to upload dataset');
    } finally {
      setUploading(false);
    }
  }

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
    setQueryLoading(true);

    try {
      const response = await fetch(`${apiBase}/datasets/${activeDatasetId}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql: querySql }),
      });

      if (!response.ok) {
        throw new Error(`Query failed (${response.status})`);
      }

      const result = (await response.json()) as QueryResult;
      setQueryResult(result);
      onStatusChange?.(`Query completed with ${result.row_count} row${result.row_count === 1 ? '' : 's'}`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Failed to run query');
    } finally {
      setQueryLoading(false);
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
          {loadingDatasets ? 'Loading recent datasets...' : `${datasets.length} recent dataset${datasets.length === 1 ? '' : 's'}`}
        </div>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <form className="space-y-5" onSubmit={handleUpload}>
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
          ) : null}

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
              {datasets.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-4 text-sm text-slate-400">
                  No datasets registered yet. Upload the first CSV to begin the flow.
                </div>
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
              <div className="mt-4 rounded-xl border border-dashed border-white/10 bg-slate-950/50 p-4 text-sm leading-6 text-slate-400">
                Upload a CSV to see row counts, quality score, and storage details here.
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
              <div className="mt-4 overflow-auto rounded-xl border border-white/10">
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
            ) : (
              <div className="mt-4 rounded-xl border border-dashed border-white/10 bg-slate-950/50 p-4 text-sm leading-6 text-slate-400">
                Select a dataset, tune the SQL in Query builder, then run the query to preview rows here.
              </div>
            )}
          </div>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
    </section>
  );
}

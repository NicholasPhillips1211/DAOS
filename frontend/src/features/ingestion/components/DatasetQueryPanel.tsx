import { inputClass, WorkflowState } from '../../../components/ui';
import type { IngestionWizardViewModel } from '../hooks/useIngestionWizard';

type DatasetQueryPanelProps = {
  wizard: IngestionWizardViewModel;
};

export function DatasetQueryPanel({ wizard }: DatasetQueryPanelProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm uppercase tracking-[0.25em] text-slate-300">Recent datasets</h3>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
          Workspace #{wizard.workspaceId}
        </span>
      </div>
      <label className="mt-4 block space-y-2">
        <span className="text-xs uppercase tracking-[0.2em] text-slate-400">Dataset for query runner</span>
        <select
          value={wizard.selectedDatasetId}
          onChange={(event) => wizard.setSelectedDatasetId(event.target.value)}
          className={inputClass}
        >
          <option value="">Select dataset</option>
          {wizard.datasets.map((dataset) => (
            <option key={dataset.id} value={dataset.id}>
              {dataset.name} (ID {dataset.id})
            </option>
          ))}
        </select>
      </label>

      <DatasetList wizard={wizard} />

      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={wizard.runQuery}
          disabled={!wizard.activeDatasetId || wizard.queryLoading}
          className="rounded-full bg-emerald-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {wizard.queryLoading ? 'Running query...' : 'Run query now'}
        </button>
        <button
          type="button"
          onClick={() => wizard.onPrepareDashboard?.(wizard.datasetName)}
          className="rounded-full border border-white/20 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-cyan-300/50"
        >
          Use for dashboard
        </button>
      </div>
    </div>
  );
}

function DatasetList({ wizard }: DatasetQueryPanelProps) {
  if (wizard.loadingDatasets) {
    return (
      <div className="mt-4">
        <WorkflowState
          variant="loading"
          title="Loading datasets"
          description="Fetching recent workspace datasets so you can choose one for query and dashboard creation."
        />
      </div>
    );
  }

  if (wizard.datasets.length === 0) {
    return (
      <div className="mt-4">
        <WorkflowState
          variant="empty"
          title="No datasets yet"
          description="Upload the first CSV to begin the flow and make the query runner available."
          action={
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
              After upload, the next step is {wizard.nextStage.label.toLowerCase()}.
            </p>
          }
        />
      </div>
    );
  }

  return (
    <div className="mt-4 space-y-3">
      {wizard.datasets.map((dataset) => (
        <div key={dataset.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-medium text-white">{dataset.name}</p>
              <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-400">
                {dataset.source_type} - {dataset.state}
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
      ))}
    </div>
  );
}

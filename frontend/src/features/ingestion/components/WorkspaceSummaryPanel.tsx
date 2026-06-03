import { WorkflowState } from '../../../components/ui';
import type { IngestionWizardViewModel } from '../hooks/useIngestionWizard';

type WorkspaceSummaryPanelProps = {
  wizard: IngestionWizardViewModel;
};

export function WorkspaceSummaryPanel({ wizard }: WorkspaceSummaryPanelProps) {
  const { workspaceSummary } = wizard;

  if (!workspaceSummary) {
    return null;
  }

  if (!workspaceSummary.has_datasets) {
    return (
      <WorkflowState
        variant="empty"
        title="No datasets yet"
        description={workspaceSummary.recommended_next_action}
      />
    );
  }

  return (
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
  );
}

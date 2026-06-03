import { WorkflowState } from '../../../components/ui';
import { DashboardDraftPanel } from './DashboardDraftPanel';
import type { IngestionWizardViewModel } from '../hooks/useIngestionWizard';

type QueryResultPanelProps = {
  wizard: IngestionWizardViewModel;
};

export function QueryResultPanel({ wizard }: QueryResultPanelProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm uppercase tracking-[0.25em] text-slate-300">Query result</h3>
        <span className="rounded-full border border-white/10 bg-slate-950/60 px-3 py-1 text-xs text-slate-300">
          {wizard.queryResult
            ? `${wizard.queryResult.row_count} row${wizard.queryResult.row_count === 1 ? '' : 's'}`
            : 'No query run'}
        </span>
      </div>

      {wizard.queryResult ? (
        <div className="mt-4 space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={wizard.previewDashboardDraft}
              disabled={wizard.draftPreviewLoading}
              className="rounded-full bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {wizard.draftPreviewLoading ? 'Building draft preview...' : 'Preview dashboard draft'}
            </button>
            <span className="text-xs text-slate-400">
              Generates a recommended chart-backed draft that must be verified before approval.
            </span>
          </div>

          <DashboardDraftPanel wizard={wizard} />
          <QueryResultTable wizard={wizard} />
        </div>
      ) : (
        <div className="mt-4">
          <WorkflowState
            variant="empty"
            title="No query result yet"
            description="Select a dataset, tune the SQL in Query builder, then run the query to preview rows here."
            action={
              <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
                The next action is {wizard.queryResult ? 'preview dashboard draft' : 'run the query'}.
              </p>
            }
          />
        </div>
      )}
    </div>
  );
}

function QueryResultTable({ wizard }: QueryResultPanelProps) {
  const result = wizard.queryResult;

  if (!result) {
    return null;
  }

  return (
    <div className="overflow-auto rounded-xl border border-white/10">
      <table className="w-full border-collapse text-left text-sm text-slate-200">
        <thead className="bg-slate-950/70 text-xs uppercase tracking-[0.2em] text-slate-400">
          <tr>
            {result.columns.map((column) => (
              <th key={column} className="px-3 py-2 font-medium">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {result.rows.slice(0, 10).map((row, rowIndex) => (
            <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white/5' : 'bg-transparent'}>
              {result.columns.map((column) => (
                <td key={`${rowIndex}-${column}`} className="px-3 py-2 text-slate-300">
                  {String(row[column] ?? 'No value')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

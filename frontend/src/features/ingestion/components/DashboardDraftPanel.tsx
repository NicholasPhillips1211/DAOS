import { inputClass } from '../../../components/ui';
import type { IngestionWizardViewModel } from '../hooks/useIngestionWizard';

type DashboardDraftPanelProps = {
  wizard: IngestionWizardViewModel;
};

export function DashboardDraftPanel({ wizard }: DashboardDraftPanelProps) {
  const draft = wizard.dashboardDraftPreview;

  if (!draft) {
    return null;
  }

  return (
    <div className="rounded-xl border border-cyan-300/20 bg-cyan-400/10 p-4 text-sm text-slate-100">
      <p className="text-xs uppercase tracking-[0.2em] text-cyan-100">Draft preview</p>
      <div className="mt-3 space-y-3">
        <label className="block space-y-2">
          <span className="text-xs uppercase tracking-[0.2em] text-slate-300">Dashboard title</span>
          <input
            value={draft.name}
            onChange={(event) => wizard.updateDashboardDraftPreview({ name: event.target.value })}
            className={inputClass}
          />
        </label>
        <label className="block space-y-2">
          <span className="text-xs uppercase tracking-[0.2em] text-slate-300">Dashboard description</span>
          <textarea
            value={draft.description}
            onChange={(event) => wizard.updateDashboardDraftPreview({ description: event.target.value })}
            className={`${inputClass} min-h-24 resize-y`}
          />
        </label>
      </div>

      {draft.recommendation ? (
        <div className="mt-3 rounded-lg border border-white/15 bg-slate-950/50 p-3">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Chart recommendation</p>
          <p className="mt-1 text-sm font-medium text-white">{draft.recommendation.chartType}</p>
          <p className="mt-1 text-sm text-slate-300">{draft.recommendation.reason}</p>
          {draft.recommendation.bestPractices.length > 0 ? (
            <ul className="mt-3 space-y-2 text-sm text-slate-300">
              {draft.recommendation.bestPractices.map((practice) => (
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
          checked={wizard.approvalChecked}
          onChange={(event) => wizard.setApprovalChecked(event.target.checked)}
          className="mt-1 h-4 w-4 rounded border-white/20 bg-slate-950/70"
        />
        I verified this draft preview and approve dashboard creation.
      </label>

      <button
        type="button"
        onClick={wizard.createDashboardFromQuery}
        disabled={wizard.dashboardCreatingFromQuery || !wizard.approvalChecked}
        className="mt-4 rounded-full bg-emerald-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {wizard.dashboardCreatingFromQuery ? 'Creating dashboard...' : 'Approve and create dashboard'}
      </button>
    </div>
  );
}

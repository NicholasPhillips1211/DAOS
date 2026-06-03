import type { IngestionWizardViewModel } from '../hooks/useIngestionWizard';

type QueryBuilderPanelProps = {
  wizard: IngestionWizardViewModel;
};

export function QueryBuilderPanel({ wizard }: QueryBuilderPanelProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm uppercase tracking-[0.25em] text-slate-300">Query builder</h3>
        <span className="rounded-full border border-white/10 bg-slate-950/60 px-3 py-1 text-xs text-slate-300">
          Suggested starting point
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-400">
        Use the detected columns to move straight into analysis. This template can be pasted into the lakehouse query
        endpoint or adapted for a dashboard metric.
      </p>
      <textarea
        value={wizard.querySql}
        onChange={(event) => wizard.setQuerySql(event.target.value)}
        className="mt-4 min-h-36 w-full resize-y rounded-xl border border-white/10 bg-slate-950/70 p-4 font-mono text-xs leading-6 text-cyan-100 outline-none focus:border-cyan-300/50"
      />
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => wizard.setQuerySql(wizard.queryTemplate)}
          className="rounded-full border border-white/20 bg-white/5 px-4 py-2 text-xs font-semibold text-slate-200 transition hover:border-cyan-300/50"
        >
          Reset to template
        </button>
        <span className="text-xs text-slate-400">The query endpoint reads from a virtual table named dataset.</span>
      </div>
    </div>
  );
}

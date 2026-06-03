import type { WorkspaceWorkflow } from '../../hooks/useWorkspaceWorkflow';

type AutomationPlanSummaryProps = {
  workflow: WorkspaceWorkflow;
};

export function AutomationPlanSummary({ workflow }: AutomationPlanSummaryProps) {
  const { latestAutomationPlan, parsedAutomation } = workflow;

  return (
    <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm uppercase tracking-[0.25em] text-slate-300">Latest automation</h3>
        <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-300">
          {latestAutomationPlan ? latestAutomationPlan.status : 'empty'}
        </span>
      </div>
      {parsedAutomation ? (
        <div className="mt-4 space-y-4 text-sm text-slate-200">
          <div>
            <p className="text-lg font-semibold text-white">{parsedAutomation.title}</p>
            <p className="mt-1 leading-6 text-slate-300">{parsedAutomation.summary}</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <MetricTile label="Automation score" value={parsedAutomation.automation_score} />
            <MetricTile label="Model" value={latestAutomationPlan?.model_name ?? 'heuristic fallback'} />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Next steps</p>
            <ul className="mt-2 space-y-2">
              {parsedAutomation.next_steps.map((step) => (
                <li key={step} className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-slate-200">
                  {step}
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : (
        <p className="mt-4 text-sm leading-6 text-slate-400">No automation plan generated yet.</p>
      )}
    </div>
  );
}

function MetricTile({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-3">
      <p className="text-xs uppercase tracking-[0.25em] text-slate-400">{label}</p>
      <p className="mt-1 text-sm font-semibold text-white">{value}</p>
    </div>
  );
}

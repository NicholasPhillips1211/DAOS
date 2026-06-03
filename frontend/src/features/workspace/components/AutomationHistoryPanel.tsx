import { cardClass } from '../../../components/ui';
import type { WorkspaceWorkflow } from '../hooks/useWorkspaceWorkflow';

type AutomationHistoryPanelProps = {
  workflow: WorkspaceWorkflow;
};

export function AutomationHistoryPanel({ workflow }: AutomationHistoryPanelProps) {
  const { automationPlans } = workflow;

  return (
    <section className={cardClass}>
      <p className="text-xs uppercase tracking-[0.35em] text-violet-200/90">Recent Automations</p>
      <h3 className="mt-2 text-xl font-semibold text-white">Generated plans</h3>
      <ul className="mt-4 space-y-3 text-sm text-slate-200">
        {automationPlans.length === 0 ? <li className="text-slate-400">No automation plans yet.</li> : null}
        {automationPlans.map((item) => (
          <li key={item.id} className="rounded-2xl border border-white/10 bg-white/5 p-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium text-white">{item.objective}</p>
                <p className="mt-1 text-slate-400">{item.summary}</p>
              </div>
              <span className="rounded-full border border-white/10 bg-slate-950/60 px-2 py-1 text-xs text-slate-300">
                {item.provider}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

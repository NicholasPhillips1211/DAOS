import { cardClass, inputClass, Tooltip } from '../../../components/ui';
import { dashboardTemplates } from '../dashboardTemplates';
import type { WorkspaceWorkflow } from '../../workspace/hooks/useWorkspaceWorkflow';

type DashboardOperationsPanelProps = {
  workflow: WorkspaceWorkflow;
};

export function DashboardOperationsPanel({ workflow }: DashboardOperationsPanelProps) {
  const {
    applyDashboardTemplate,
    createDashboard,
    dashboardDescription,
    dashboardLoading,
    dashboardName,
    dashboardSectionRef,
    dashboards,
    selectedDashboardTemplate,
    setDashboardDescription,
    setDashboardName,
  } = workflow;

  return (
    <section className={cardClass} ref={dashboardSectionRef}>
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-cyan-200/90">Recent Dashboards</p>
          <h3 className="mt-2 text-xl font-semibold text-white">Live dashboard records</h3>
        </div>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
          {dashboards.length}
        </span>
      </div>
      <form className="mt-4 space-y-3" onSubmit={createDashboard}>
        <div className="rounded-2xl border border-cyan-300/20 bg-cyan-400/10 p-3">
          <p className="text-xs uppercase tracking-[0.25em] text-cyan-100">Starter templates</p>
          <p className="mt-2 text-sm leading-6 text-slate-200">
            Pick a preset to seed the dashboard name and description, then refine it before saving.
          </p>
          <div className="mt-3 grid gap-2">
            {dashboardTemplates.map((template) => {
              const isSelected = selectedDashboardTemplate === template.id;

              return (
                <button
                  key={template.id}
                  type="button"
                  onClick={() => applyDashboardTemplate(template.id)}
                  className={`rounded-xl border px-3 py-3 text-left transition ${
                    isSelected
                      ? 'border-cyan-300/50 bg-cyan-400/15 text-white'
                      : 'border-white/10 bg-slate-950/55 text-slate-300 hover:border-cyan-300/30 hover:bg-white/5'
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm font-semibold">{template.label}</span>
                    <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[11px] uppercase tracking-[0.2em] text-slate-400">
                      {isSelected ? 'Selected' : 'Use'}
                    </span>
                  </div>
                  <p className="mt-1 text-xs leading-5 text-inherit/80">{template.note}</p>
                </button>
              );
            })}
          </div>
        </div>
        <input
          value={dashboardName}
          onChange={(event) => setDashboardName(event.target.value)}
          className={inputClass}
          placeholder="Dashboard name"
        />
        <textarea
          value={dashboardDescription}
          onChange={(event) => setDashboardDescription(event.target.value)}
          className={`${inputClass} min-h-24 resize-y`}
          placeholder="Dashboard description"
        />
        <Tooltip content="Save this dashboard configuration to your workspace">
          <button
            type="submit"
            disabled={dashboardLoading}
            className="rounded-full bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {dashboardLoading ? 'Creating...' : 'Create dashboard'}
          </button>
        </Tooltip>
      </form>
      <ul className="mt-5 space-y-2 text-sm text-slate-200">
        {dashboards.length === 0 ? <li className="text-slate-400">No dashboards yet.</li> : null}
        {dashboards.map((item) => (
          <li key={item.id} className="rounded-2xl border border-white/10 bg-white/5 p-3">
            <p className="font-medium text-white">{item.name}</p>
            <p className="mt-1 text-slate-400">{item.description ?? 'No description'}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}

import type { WorkspaceWorkflow } from '../../hooks/useWorkspaceWorkflow';

type AutomationSignalsPanelProps = {
  workflow: WorkspaceWorkflow;
};

export function AutomationSignalsPanel({ workflow }: AutomationSignalsPanelProps) {
  const { parsedAutomation } = workflow;
  const signals = parsedAutomation?.signals ? Object.entries(parsedAutomation.signals).slice(0, 6) : [];

  return (
    <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
      <p className="text-sm uppercase tracking-[0.25em] text-slate-300">Signals used</p>
      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm text-slate-200">
        {signals.map(([key, value]) => (
          <div key={key} className="rounded-xl border border-white/10 bg-white/5 p-3">
            <dt className="text-xs uppercase tracking-[0.22em] text-slate-400">{key.replace(/_/g, ' ')}</dt>
            <dd className="mt-1 text-lg font-semibold text-white">{value}</dd>
          </div>
        ))}
        {parsedAutomation?.provider_notes ? (
          <div className="col-span-2 rounded-xl border border-cyan-300/15 bg-cyan-400/10 p-3 text-slate-200">
            {parsedAutomation.provider_notes}
          </div>
        ) : (
          <div className="col-span-2 rounded-xl border border-white/10 bg-white/5 p-3 text-slate-400">
            The latest plan will show the LM Studio or fallback reasoning here.
          </div>
        )}
      </dl>
    </div>
  );
}

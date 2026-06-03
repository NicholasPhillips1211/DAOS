import { Tooltip } from '../../../../components/ui';
import type { WorkspaceWorkflow } from '../../hooks/useWorkspaceWorkflow';

type AutomationExecutionPanelProps = {
  workflow: WorkspaceWorkflow;
};

export function AutomationExecutionPanel({ workflow }: AutomationExecutionPanelProps) {
  const { automationExecuting, executeAutomation, latestAutomationPlan } = workflow;

  if (!latestAutomationPlan) {
    return null;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Execution</p>
        <div className="mt-4 space-y-4">
          <div>
            <p className="text-sm text-slate-300">
              Status: <span className="font-medium text-white">{latestAutomationPlan.execution_status ?? 'Not executed'}</span>
            </p>
            {latestAutomationPlan.executed_at ? (
              <p className="mt-1 text-xs text-slate-400">
                Executed at: {new Date(latestAutomationPlan.executed_at).toLocaleString()}
              </p>
            ) : null}
          </div>
          <Tooltip content="Run this automation plan immediately in your workspace">
            <button
              onClick={executeAutomation}
              disabled={automationExecuting || latestAutomationPlan.execution_status === 'completed'}
              className="w-full rounded-full bg-emerald-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {getExecutionLabel(automationExecuting, latestAutomationPlan.execution_status)}
            </button>
          </Tooltip>
        </div>
      </div>

      {latestAutomationPlan.execution_results_json ? (
        <div className="rounded-2xl border border-emerald-300/20 bg-emerald-400/10 p-4">
          <p className="text-xs uppercase tracking-[0.25em] text-emerald-200">Execution results</p>
          <pre className="mt-3 max-h-48 overflow-auto rounded-lg border border-white/10 bg-slate-950/60 p-3 text-xs text-slate-200">
            {formatExecutionResults(latestAutomationPlan.execution_results_json)}
          </pre>
        </div>
      ) : null}
    </div>
  );
}

function getExecutionLabel(isExecuting: boolean, status?: string | null): string {
  if (isExecuting) {
    return 'Executing...';
  }
  return status === 'completed' ? 'Already executed' : 'Execute plan now';
}

function formatExecutionResults(value: string): string {
  try {
    return JSON.stringify(JSON.parse(value), null, 2);
  } catch {
    return value;
  }
}

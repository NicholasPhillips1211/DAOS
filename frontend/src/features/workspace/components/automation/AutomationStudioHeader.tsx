import { inputClass, Tooltip } from '../../../../components/ui';
import type { WorkspaceWorkflow } from '../../hooks/useWorkspaceWorkflow';

type AutomationStudioHeaderProps = {
  workflow: WorkspaceWorkflow;
};

export function AutomationStudioHeader({ workflow }: AutomationStudioHeaderProps) {
  return (
    <>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-cyan-200/90">Automation Studio</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">Generate an operational plan</h2>
          <p className="mt-1 text-sm leading-6 text-slate-300">
            The backend tries a local LM Studio-compatible model first, then uses a deterministic fallback if the
            model server is offline.
          </p>
        </div>
        <div className="rounded-full border border-amber-300/20 bg-amber-400/10 px-4 py-2 text-sm text-amber-100">
          Provider: {workflow.latestAutomationPlan?.provider ?? 'pending'}
        </div>
      </div>

      <form className="space-y-4" onSubmit={workflow.generateAutomation}>
        <textarea
          value={workflow.automationObjective}
          onChange={(event) => workflow.setAutomationObjective(event.target.value)}
          className={`${inputClass} min-h-28 resize-y`}
          placeholder="Describe what you want the workspace to automate"
        />
        <div className="flex flex-wrap gap-3">
          <Tooltip content="Create an AI-powered automation plan for your workspace">
            <button
              type="submit"
              disabled={workflow.automationLoading}
              className="rounded-full bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {workflow.automationLoading ? 'Generating...' : 'Generate automation plan'}
            </button>
          </Tooltip>
          <span className="self-center text-sm text-slate-400">
            Local AI support is controlled by the backend `LLM_*` settings.
          </span>
        </div>
      </form>
    </>
  );
}

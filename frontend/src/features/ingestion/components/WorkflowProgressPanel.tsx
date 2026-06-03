import { wizardStages } from '../constants';
import type { IngestionWizardViewModel } from '../hooks/useIngestionWizard';

type WorkflowProgressPanelProps = {
  wizard: IngestionWizardViewModel;
};

export function WorkflowProgressPanel({ wizard }: WorkflowProgressPanelProps) {
  return (
    <div className="rounded-2xl border border-cyan-300/20 bg-cyan-400/10 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-cyan-100">Workflow progress</p>
          <p className="mt-1 text-sm text-slate-100">
            You are on <span className="font-semibold text-white">{wizardStages[wizard.currentStageIndex]?.label}</span>.
          </p>
        </div>
        <div className="rounded-full border border-white/10 bg-slate-950/60 px-3 py-1 text-xs text-slate-300">
          Next: {wizard.nextStage.label}
        </div>
      </div>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-950/70">
        <div className="h-full rounded-full bg-gradient-to-r from-cyan-300 to-emerald-300" style={{ width: `${wizard.progressPercent}%` }} />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {wizardStages.map((stage, index) => {
          const isActive = stage.id === wizard.currentStage;
          const isComplete = index < wizard.currentStageIndex;

          return (
            <div
              key={stage.id}
              className={`rounded-xl border p-3 ${
                isActive
                  ? 'border-cyan-300/40 bg-cyan-400/15 text-white'
                  : isComplete
                    ? 'border-emerald-300/20 bg-emerald-400/10 text-emerald-50'
                    : 'border-white/10 bg-slate-950/50 text-slate-300'
              }`}
            >
              <p className="text-[11px] uppercase tracking-[0.25em]">{stage.label}</p>
              <p className="mt-2 text-xs leading-5 text-inherit/90">{stage.detail}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

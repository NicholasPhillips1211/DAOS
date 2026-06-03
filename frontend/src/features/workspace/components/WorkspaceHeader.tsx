import { inputClass, Tooltip } from '../../../components/ui';

type WorkspaceHeaderProps = {
  workspaceId: string;
  workspaceSignals: {
    dashboards: number;
    comments: number;
    shares: number;
    automations: number;
  };
  onExitWorkspace: () => void;
  onWorkspaceIdChange: (value: string) => void;
};

export function WorkspaceHeader({
  workspaceId,
  workspaceSignals,
  onExitWorkspace,
  onWorkspaceIdChange,
}: WorkspaceHeaderProps) {
  return (
    <header className="rounded-[2rem] border border-white/10 bg-slate-950/70 p-6 shadow-[0_30px_120px_rgba(0,0,0,0.35)] backdrop-blur-xl">
      <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex items-start gap-4">
          <Tooltip content="Go back to home page">
            <button
              onClick={onExitWorkspace}
              className="mt-2 text-sm font-medium text-slate-400 transition hover:text-cyan-300"
            >
              Back to Home
            </button>
          </Tooltip>
          <div className="max-w-4xl">
            <p className="text-xs uppercase tracking-[0.5em] text-cyan-200/90">DAOS Control Room</p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-white md:text-5xl">
              Operate dashboards, automation, and local AI from one workspace.
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-7 text-slate-300 md:text-lg">
              Create dashboards, capture collaboration, and generate automation plans backed by a local
              LM Studio-compatible model or a deterministic fallback when no model server is available.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <span className="rounded-full border border-cyan-300/20 bg-cyan-400/10 px-3 py-1 text-xs text-cyan-100">
                FastAPI control plane
              </span>
              <span className="rounded-full border border-emerald-300/20 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-100">
                React analyst UI
              </span>
              <span className="rounded-full border border-amber-300/20 bg-amber-400/10 px-3 py-1 text-xs text-amber-100">
                LM Studio ready
              </span>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200">
                Workspace #{workspaceId}
              </span>
            </div>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[24rem]">
          <label className="space-y-2 rounded-2xl border border-white/10 bg-white/5 p-4">
            <span className="text-xs uppercase tracking-[0.3em] text-slate-400">Workspace ID</span>
            <input
              value={workspaceId}
              onChange={(event) => onWorkspaceIdChange(event.target.value)}
              className={inputClass}
              inputMode="numeric"
            />
          </label>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Live signals</p>
            <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
              <SignalTile label="Dashboards" value={workspaceSignals.dashboards} />
              <SignalTile label="Automations" value={workspaceSignals.automations} />
              <SignalTile label="Comments" value={workspaceSignals.comments} />
              <SignalTile label="Shares" value={workspaceSignals.shares} />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

function SignalTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2">
      <p className="text-slate-400">{label}</p>
      <p className="text-lg font-semibold text-white">{value}</p>
    </div>
  );
}

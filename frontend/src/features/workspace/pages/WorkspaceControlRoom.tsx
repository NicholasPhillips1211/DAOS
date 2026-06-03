import { cardClass } from '../../../components/ui';
import { AiBridgePanel } from '../../copilot/components/AiBridgePanel';
import { DashboardOperationsPanel } from '../../dashboards/components/DashboardOperationsPanel';
import { IngestionWizard } from '../../ingestion/IngestionWizard';
import { AutomationHistoryPanel } from '../components/AutomationHistoryPanel';
import { AutomationStudio } from '../components/AutomationStudio';
import { CollaborationPanel } from '../components/CollaborationPanel';
import { WorkspaceHeader } from '../components/WorkspaceHeader';
import { useWorkspaceWorkflow } from '../hooks/useWorkspaceWorkflow';

type WorkspaceControlRoomProps = {
  onExitWorkspace: () => void;
};

export function WorkspaceControlRoom({ onExitWorkspace }: WorkspaceControlRoomProps) {
  const workflow = useWorkspaceWorkflow();

  return (
    <main className="relative min-h-screen overflow-hidden text-slate-100">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-[-8rem] top-[-8rem] h-72 w-72 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="absolute right-[-5rem] top-20 h-80 w-80 rounded-full bg-amber-300/15 blur-3xl" />
        <div className="absolute bottom-[-6rem] left-1/3 h-96 w-96 rounded-full bg-emerald-400/10 blur-3xl" />
      </div>

      <section className="relative mx-auto w-full max-w-7xl px-6 py-8 lg:px-10 lg:py-10">
        <WorkspaceHeader
          workspaceId={workflow.workspaceId}
          workspaceSignals={workflow.workspaceSignals}
          onExitWorkspace={onExitWorkspace}
          onWorkspaceIdChange={workflow.setWorkspaceId}
        />

        <div className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <section className={`${cardClass} space-y-5`}>
            <IngestionWizard
              apiBase={workflow.apiBase}
              workspaceId={workflow.workspaceIdNumber || 1}
              userEmail={workflow.commentEmail}
              onPrepareDashboard={workflow.prepareDashboardFromDataset}
              onStatusChange={workflow.setStatus}
              onPreviewDashboardFromQuery={workflow.previewDashboardFromQueryBlueprint}
              onCreateDashboardFromQuery={workflow.createDashboardFromQueryBlueprint}
            />

            <AutomationStudio workflow={workflow} />
          </section>

          <aside className="space-y-6">
            <AiBridgePanel />
            <DashboardOperationsPanel workflow={workflow} />
            <CollaborationPanel workflow={workflow} />
            <AutomationHistoryPanel workflow={workflow} />
          </aside>
        </div>

        <footer className="mt-6 rounded-[1.5rem] border border-white/10 bg-slate-950/70 p-4 text-sm text-slate-300 backdrop-blur">
          <p>Status: {workflow.status}</p>
          {workflow.error ? <p className="mt-1 text-rose-300">Error: {workflow.error}</p> : null}
          <p className="mt-1 text-slate-400">API Base: {workflow.apiBase}</p>
        </footer>
      </section>
    </main>
  );
}

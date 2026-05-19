import { FormEvent, useMemo, useRef, useState } from 'react';
import { HomeView } from './HomeView';
import { GuidedTour } from './GuidedTour';
import { IngestionWizard } from './IngestionWizard';
import { Tooltip } from './Tooltip';
import { useGuidedTour } from './useGuidedTour';
import {
  createCommentRecord,
  createDashboardRecord,
  createShareRecord,
  executeAutomationPlan,
  generateAutomationPlan,
  recommendChart,
} from './features/workspace/api';
import {
  AutomationPlanPayload,
  AutomationPlanRecord,
  ChartRecommendationRead,
  CommentRecord,
  DashboardDraftPreview,
  DashboardRecord,
  ShareRecord,
} from './types/domain';

const apiBase = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

const inputClass =
  'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-cyan-300/60 focus:bg-white/8';

const cardClass = 'rounded-[1.75rem] border border-white/10 bg-slate-950/65 p-5 shadow-[0_24px_90px_rgba(0,0,0,0.25)] backdrop-blur';

type DashboardTemplate = {
  id: string;
  label: string;
  name: string;
  description: string;
  note: string;
};

// These presets speed up dashboard creation by giving the user a few opinionated starting points.
const dashboardTemplates: DashboardTemplate[] = [
  {
    id: 'executive-summary',
    label: 'Executive summary',
    name: 'Executive Overview',
    description: 'Weekly KPI summary for leadership with the highest-level trends and exceptions.',
    note: 'Good for quick stakeholder review.',
  },
  {
    id: 'operations-review',
    label: 'Operations review',
    name: 'Operations Control Panel',
    description: 'Daily health view for operational metrics, alerts, and exceptions that need action.',
    note: 'Best for teams handling live operations.',
  },
  {
    id: 'analysis-deep-dive',
    label: 'Analysis deep dive',
    name: 'Trend Deep Dive',
    description: 'Exploratory dashboard for comparison, segmentation, and root-cause analysis.',
    note: 'Useful when a query needs follow-up investigation.',
  },
];

function parseAutomationPayload(value: string): AutomationPlanPayload | null {
  try {
    return JSON.parse(value) as AutomationPlanPayload;
  } catch {
    return null;
  }
}

export default function App() {
  const [showWorkspace, setShowWorkspace] = useState(false);
  const tour = useGuidedTour();
  const dashboardSectionRef = useRef<HTMLElement | null>(null);
  const [workspaceId, setWorkspaceId] = useState('1');
  const [dashboardName, setDashboardName] = useState('Executive Overview');
  const [dashboardDescription, setDashboardDescription] = useState('Weekly KPI summary for leadership');
  const [selectedDashboardTemplate, setSelectedDashboardTemplate] = useState(dashboardTemplates[0].id);
  const [dashboards, setDashboards] = useState<DashboardRecord[]>([]);

  const [commentEmail, setCommentEmail] = useState('analyst@daos.local');
  const [commentMessage, setCommentMessage] = useState('Revenue panel should include a MoM trend.');
  const [comments, setComments] = useState<CommentRecord[]>([]);

  const [shareEmail, setShareEmail] = useState('stakeholder@daos.local');
  const [sharePermission, setSharePermission] = useState('view');
  const [shares, setShares] = useState<ShareRecord[]>([]);

  const [automationObjective, setAutomationObjective] = useState('Automate daily workspace triage, dashboard refreshes, and stakeholder updates');
  const [automationPlans, setAutomationPlans] = useState<AutomationPlanRecord[]>([]);

  const [status, setStatus] = useState('Ready');
  const [error, setError] = useState<string | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [commentLoading, setCommentLoading] = useState(false);
  const [shareLoading, setShareLoading] = useState(false);
  const [automationLoading, setAutomationLoading] = useState(false);
  const [automationExecuting, setAutomationExecuting] = useState(false);

  const workspaceIdNumber = useMemo(() => Number(workspaceId), [workspaceId]);
  const latestAutomationPlan = automationPlans[0];
  const parsedAutomation = useMemo(
    () => (latestAutomationPlan ? parseAutomationPayload(latestAutomationPlan.automation_json) : null),
    [latestAutomationPlan],
  );

  const workspaceSignals = {
    dashboards: dashboards.length,
    comments: comments.length,
    shares: shares.length,
    automations: automationPlans.length,
  };

  function focusDashboardForm(): void {
    dashboardSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // Keep form submit handlers thin: validate UI state, delegate network work to API modules, and update local view state.
  async function createDashboard(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!Number.isFinite(workspaceIdNumber)) {
      setError('Workspace ID must be a number.');
      return;
    }
    setError(null);
    setDashboardLoading(true);
    try {
      const record = await createDashboardRecord(apiBase, commentEmail, {
        workspace_id: workspaceIdNumber,
        name: dashboardName,
        description: dashboardDescription,
      });
      setDashboards((previous) => [record, ...previous].slice(0, 6));
      setStatus(`Dashboard created: ${record.name}`);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Failed to create dashboard';
      setError(message);
    } finally {
      setDashboardLoading(false);
    }
  }

  async function postComment(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!Number.isFinite(workspaceIdNumber)) {
      setError('Workspace ID must be a number.');
      return;
    }
    setError(null);
    setCommentLoading(true);
    try {
      const latestDashboard = dashboards[0];
      const record = await createCommentRecord(apiBase, commentEmail, {
        workspace_id: workspaceIdNumber,
        resource_type: 'dashboard',
        resource_id: latestDashboard?.id ?? 1,
        user_email: commentEmail,
        message: commentMessage,
      });
      setComments((previous) => [record, ...previous].slice(0, 6));
      setStatus(`Comment added by ${record.user_email}`);
      setCommentMessage('');
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Failed to post comment';
      setError(message);
    } finally {
      setCommentLoading(false);
    }
  }

  async function createShare(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!Number.isFinite(workspaceIdNumber)) {
      setError('Workspace ID must be a number.');
      return;
    }
    setError(null);
    setShareLoading(true);
    try {
      const latestDashboard = dashboards[0];
      const record = await createShareRecord(apiBase, commentEmail, {
        workspace_id: workspaceIdNumber,
        resource_type: 'dashboard',
        resource_id: latestDashboard?.id ?? 1,
        target_email: shareEmail,
        permission: sharePermission,
      });
      setShares((previous) => [record, ...previous].slice(0, 6));
      setStatus(`Shared dashboard with ${record.target_email}`);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Failed to create share';
      setError(message);
    } finally {
      setShareLoading(false);
    }
  }

  async function generateAutomation(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!Number.isFinite(workspaceIdNumber)) {
      setError('Workspace ID must be a number.');
      return;
    }
    setError(null);
    setAutomationLoading(true);
    try {
      const record = await generateAutomationPlan(apiBase, commentEmail, {
        workspace_id: workspaceIdNumber,
        objective: automationObjective,
      });
      setAutomationPlans((previous) => [record, ...previous].slice(0, 6));
      setStatus(`Automation generated via ${record.provider}`);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Failed to generate automation plan';
      setError(message);
    } finally {
      setAutomationLoading(false);
    }
  }

  async function executeAutomation(): Promise<void> {
    if (!latestAutomationPlan) {
      setError('No automation plan to execute.');
      return;
    }
    setError(null);
    setAutomationExecuting(true);
    try {
      const updated = await executeAutomationPlan(apiBase, commentEmail, latestAutomationPlan.id);
      setAutomationPlans((previous) =>
        previous.map((plan) => (plan.id === updated.id ? updated : plan)),
      );
      setStatus(`Automation executed successfully at ${updated.executed_at}`);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Failed to execute automation plan';
      setError(message);
    } finally {
      setAutomationExecuting(false);
    }
  }

  // This helper keeps the dashboard panel synchronized with the ingestion wizard handoff.
  function prepareDashboardFromDataset(name: string): void {
    setDashboardName(`${name} Overview`);
    setDashboardDescription(`Auto-prepared from dataset ${name}. Customize panels, then create dashboard.`);
    setStatus(`Dashboard draft prepared from dataset: ${name}`);
    focusDashboardForm();
  }

  // Template presets reduce repetitive setup and give the dashboard form a clearer starting point.
  function applyDashboardTemplate(templateId: string): void {
    const template = dashboardTemplates.find((item) => item.id === templateId);
    if (!template) {
      return;
    }

    setSelectedDashboardTemplate(template.id);
    setDashboardName(template.name);
    setDashboardDescription(template.description);
    setStatus(`Loaded dashboard template: ${template.label}`);
  }

  // The query-to-dashboard approval flow is centralized here so both draft and direct create paths share validation/loading behavior.
  async function createDashboardFromQueryBlueprint(payload: {
    datasetName: string;
    datasetId: number;
    columns: string[];
    rowCount: number;
    approvedDraft?: DashboardDraftPreview;
  }): Promise<void> {
    if (!Number.isFinite(workspaceIdNumber)) {
      throw new Error('Workspace ID must be a number.');
    }

    const draft = payload.approvedDraft ?? await previewDashboardFromQueryBlueprint(payload);

    setError(null);
    setDashboardLoading(true);
    try {
      const record = await createDashboardRecord(apiBase, commentEmail, {
        workspace_id: workspaceIdNumber,
        name: draft.name,
        description: draft.description,
      });
      setDashboards((previous) => [record, ...previous].slice(0, 6));
      setDashboardName(record.name);
      setDashboardDescription(record.description ?? draft.description);
      setStatus(`Dashboard created from query: ${record.name}`);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Failed to create dashboard from query';
      setError(message);
      throw new Error(message);
    } finally {
      setDashboardLoading(false);
    }
  }

  // Build a human-readable draft from query shape plus recommendation service output.
  async function previewDashboardFromQueryBlueprint(payload: {
    datasetName: string;
    datasetId: number;
    columns: string[];
    rowCount: number;
  }): Promise<DashboardDraftPreview> {
    const columnSummary = payload.columns.slice(0, 6).join(', ') || 'No columns';
    const recommendation = await recommendChartForQuery(payload.datasetId, payload.columns);
    const generatedName = `${payload.datasetName} Query Board`;
    const recommendationLine = recommendation
      ? ` Recommended chart: ${recommendation.chart_type} (${recommendation.reason}).`
      : '';
    const generatedDescription =
      `Auto-generated from dataset ${payload.datasetName} (ID ${payload.datasetId}). ` +
      `Result sample: ${payload.rowCount} row${payload.rowCount === 1 ? '' : 's'}. ` +
      `Suggested starter panels: ${columnSummary}.` + recommendationLine;

    setDashboardName(generatedName);
    setDashboardDescription(generatedDescription);
    focusDashboardForm();

    return {
      name: generatedName,
      description: generatedDescription,
      recommendation: recommendation
        ? {
            chartType: recommendation.chart_type,
            reason: recommendation.reason,
            bestPractices: recommendation.best_practices,
          }
        : undefined,
    };
  }

  // Recommendation failure should not block dashboard creation, so errors are intentionally swallowed to a nullable result.
  async function recommendChartForQuery(datasetId: number, columns: string[]): Promise<ChartRecommendationRead | null> {
    const xColumn = columns[0];
    if (!xColumn) {
      return null;
    }

    try {
      return await recommendChart(apiBase, commentEmail, {
        dataset_id: datasetId,
        x_column: xColumn,
        y_column: columns[1] ?? null,
        goal: 'compare',
      });
    } catch {
      return null;
    }
  }

  return (
    <>
      {!showWorkspace ? (
        <HomeView
          onStartTour={() => {
            setShowWorkspace(true);
            tour.startTour();
          }}
          onEnterWorkspace={() => setShowWorkspace(true)}
        />
      ) : (
        <main className="relative min-h-screen overflow-hidden text-slate-100">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-[-8rem] top-[-8rem] h-72 w-72 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="absolute right-[-5rem] top-20 h-80 w-80 rounded-full bg-amber-300/15 blur-3xl" />
        <div className="absolute bottom-[-6rem] left-1/3 h-96 w-96 rounded-full bg-emerald-400/10 blur-3xl" />
      </div>

      <section className="relative mx-auto w-full max-w-7xl px-6 py-8 lg:px-10 lg:py-10">
        <header className="rounded-[2rem] border border-white/10 bg-slate-950/70 p-6 shadow-[0_30px_120px_rgba(0,0,0,0.35)] backdrop-blur-xl">
          <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="flex items-start gap-4">
              <Tooltip content="Go back to home page">
                <button
                  onClick={() => setShowWorkspace(false)}
                  className="mt-2 text-sm text-slate-400 hover:text-cyan-300 transition font-medium"
                >
                  ← Back to Home
                </button>
              </Tooltip>
              <div className="max-w-4xl">
                <p className="text-xs uppercase tracking-[0.5em] text-cyan-200/90">DAOS Control Room</p>
                <h1 className="mt-3 text-4xl font-semibold tracking-tight text-white md:text-5xl">
                  Operate dashboards, automation, and local AI from one workspace.
                </h1>
                <p className="mt-4 max-w-3xl text-base leading-7 text-slate-300 md:text-lg">
                  Create dashboards, capture collaboration, and generate automation plans backed by a local LM Studio-compatible model or a deterministic fallback when no model server is available.
                </p>

                <div className="mt-6 flex flex-wrap gap-3">
                  <span className="rounded-full border border-cyan-300/20 bg-cyan-400/10 px-3 py-1 text-xs text-cyan-100">FastAPI control plane</span>
                  <span className="rounded-full border border-emerald-300/20 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-100">React analyst UI</span>
                  <span className="rounded-full border border-amber-300/20 bg-amber-400/10 px-3 py-1 text-xs text-amber-100">LM Studio ready</span>
                  <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200">Workspace #{workspaceId}</span>
                </div>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[24rem]">
              <label className="space-y-2 rounded-2xl border border-white/10 bg-white/5 p-4">
                <span className="text-xs uppercase tracking-[0.3em] text-slate-400">Workspace ID</span>
                <input
                  value={workspaceId}
                  onChange={(event) => setWorkspaceId(event.target.value)}
                  className={inputClass}
                  inputMode="numeric"
                />
              </label>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Live signals</p>
                <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2">
                    <p className="text-slate-400">Dashboards</p>
                    <p className="text-lg font-semibold text-white">{workspaceSignals.dashboards}</p>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2">
                    <p className="text-slate-400">Automations</p>
                    <p className="text-lg font-semibold text-white">{workspaceSignals.automations}</p>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2">
                    <p className="text-slate-400">Comments</p>
                    <p className="text-lg font-semibold text-white">{workspaceSignals.comments}</p>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2">
                    <p className="text-slate-400">Shares</p>
                    <p className="text-lg font-semibold text-white">{workspaceSignals.shares}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </header>

        <div className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <section className={`${cardClass} space-y-5`}>
            <IngestionWizard
              apiBase={apiBase}
              workspaceId={workspaceIdNumber || 1}
              userEmail={commentEmail}
              onPrepareDashboard={prepareDashboardFromDataset}
              onStatusChange={setStatus}
              onPreviewDashboardFromQuery={previewDashboardFromQueryBlueprint}
              onCreateDashboardFromQuery={createDashboardFromQueryBlueprint}
            />

            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-cyan-200/90">Automation Studio</p>
                <h2 className="mt-2 text-2xl font-semibold text-white">Generate an operational plan</h2>
                <p className="mt-1 text-sm leading-6 text-slate-300">
                  The backend will try a local LM Studio-compatible model first, then fall back to a deterministic plan if the model server is offline.
                </p>
              </div>
              <div className="rounded-full border border-amber-300/20 bg-amber-400/10 px-4 py-2 text-sm text-amber-100">
                Provider: {latestAutomationPlan?.provider ?? 'pending'}
              </div>
            </div>

            <form className="space-y-4" onSubmit={generateAutomation}>
              <textarea
                value={automationObjective}
                onChange={(event) => setAutomationObjective(event.target.value)}
                className={`${inputClass} min-h-28 resize-y`}
                placeholder="Describe what you want the workspace to automate"
              />
              <div className="flex flex-wrap gap-3">
                <Tooltip content="Create an AI-powered automation plan for your workspace">
                  <button
                    type="submit"
                    disabled={automationLoading}
                    className="rounded-full bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {automationLoading ? 'Generating...' : 'Generate automation plan'}
                  </button>
                </Tooltip>
                <span className="self-center text-sm text-slate-400">
                  Local AI support is controlled by the backend `LLM_*` settings.
                </span>
              </div>
            </form>

            <div className="grid gap-4 lg:grid-cols-2">
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
                      <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                        <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Automation score</p>
                        <p className="mt-1 text-2xl font-semibold text-white">{parsedAutomation.automation_score}</p>
                      </div>
                      <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                        <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Model</p>
                        <p className="mt-1 text-sm text-white">{latestAutomationPlan?.model_name ?? 'heuristic fallback'}</p>
                      </div>
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

              <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
                <p className="text-sm uppercase tracking-[0.25em] text-slate-300">Signals used</p>
                <dl className="mt-4 grid grid-cols-2 gap-3 text-sm text-slate-200">
                  {(parsedAutomation?.signals ? Object.entries(parsedAutomation.signals) : []).slice(0, 6).map(([key, value]) => (
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
            </div>

            {parsedAutomation ? (
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Triggers</p>
                  <ul className="mt-3 space-y-2 text-sm text-slate-200">
                    {parsedAutomation.triggers.map((trigger) => (
                      <li key={trigger.name} className="rounded-xl border border-white/10 bg-slate-950/60 p-3">
                        <p className="font-medium text-white">{trigger.name}</p>
                        <p className="mt-1 text-slate-400">{trigger.description}</p>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Actions</p>
                  <ul className="mt-3 space-y-2 text-sm text-slate-200">
                    {parsedAutomation.actions.map((action) => (
                      <li key={action.name} className="rounded-xl border border-white/10 bg-slate-950/60 p-3">
                        <p className="font-medium text-white">{action.name}</p>
                        <p className="mt-1 text-slate-400">{action.description}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : null}

            {latestAutomationPlan ? (
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Execution</p>
                  <div className="mt-4 space-y-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm text-slate-300">
                          Status: <span className="font-medium text-white">{latestAutomationPlan.execution_status ?? 'Not executed'}</span>
                        </p>
                        {latestAutomationPlan.executed_at && (
                          <p className="mt-1 text-xs text-slate-400">Executed at: {new Date(latestAutomationPlan.executed_at).toLocaleString()}</p>
                        )}
                      </div>
                    </div>
                    <Tooltip content="Run this automation plan immediately in your workspace">
                      <button
                        onClick={executeAutomation}
                        disabled={automationExecuting || latestAutomationPlan.execution_status === 'completed'}
                        className="rounded-full bg-emerald-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-70 w-full"
                      >
                        {automationExecuting ? 'Executing...' : latestAutomationPlan.execution_status === 'completed' ? 'Already executed' : 'Execute plan now'}
                      </button>
                    </Tooltip>
                  </div>
                </div>

                {latestAutomationPlan.execution_results_json ? (
                  <div className="rounded-2xl border border-emerald-300/20 bg-emerald-400/10 p-4">
                    <p className="text-xs uppercase tracking-[0.25em] text-emerald-200">Execution results</p>
                    <pre className="mt-3 max-h-48 overflow-auto rounded-lg border border-white/10 bg-slate-950/60 p-3 text-xs text-slate-200">
                      {typeof latestAutomationPlan.execution_results_json === 'string'
                        ? JSON.stringify(JSON.parse(latestAutomationPlan.execution_results_json), null, 2)
                        : JSON.stringify(latestAutomationPlan.execution_results_json, null, 2)}
                    </pre>
                  </div>
                ) : null}
              </div>
            ) : null}
          </section>

          <aside className="space-y-6">
            <section className={cardClass} ref={dashboardSectionRef}>
              <p className="text-xs uppercase tracking-[0.35em] text-amber-200/90">Local LLM Bridge</p>
              <h3 className="mt-2 text-2xl font-semibold text-white">LM Studio-compatible by design</h3>
              <p className="mt-3 text-sm leading-6 text-slate-300">
                Point the backend at a local OpenAI-style endpoint such as LM Studio. If it is unavailable, the app still produces a usable automation plan from workspace signals.
              </p>
              <div className="mt-4 space-y-3 text-sm text-slate-200">
                <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                  Backend endpoint: <span className="text-cyan-200">POST /api/v1/automation/generate</span>
                </div>
                <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                  Expected model server: <span className="text-amber-100">http://localhost:1234/v1</span>
                </div>
                <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                  Output format: <span className="text-emerald-100">JSON plan with triggers, actions, and next steps</span>
                </div>
              </div>
            </section>

            <section className={cardClass}>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.35em] text-cyan-200/90">Recent Dashboards</p>
                  <h3 className="mt-2 text-xl font-semibold text-white">Live dashboard records</h3>
                </div>
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">{dashboards.length}</span>
              </div>
              <form className="mt-4 space-y-3" onSubmit={createDashboard}>
                {/* The template picker reduces blank-form friction by seeding a common dashboard shape. */}
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
                <input value={dashboardName} onChange={(event) => setDashboardName(event.target.value)} className={inputClass} placeholder="Dashboard name" />
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

            <section className={cardClass}>
              <p className="text-xs uppercase tracking-[0.35em] text-emerald-200/90">Collaboration</p>
              <h3 className="mt-2 text-xl font-semibold text-white">Comments and sharing</h3>
              <div className="mt-4 grid gap-4">
                <form className="space-y-3" onSubmit={postComment}>
                  <input value={commentEmail} onChange={(event) => setCommentEmail(event.target.value)} className={inputClass} placeholder="User email" />
                  <textarea
                    value={commentMessage}
                    onChange={(event) => setCommentMessage(event.target.value)}
                    className={`${inputClass} min-h-24 resize-y`}
                    placeholder="Comment message"
                  />
                  <Tooltip content="Add a comment to foster team collaboration on dashboards">
                    <button
                      type="submit"
                      disabled={commentLoading}
                      className="rounded-full bg-emerald-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-70"
                    >
                      {commentLoading ? 'Posting...' : 'Post comment'}
                    </button>
                  </Tooltip>
                </form>

                <form className="space-y-3" onSubmit={createShare}>
                  <input value={shareEmail} onChange={(event) => setShareEmail(event.target.value)} className={inputClass} placeholder="Target email" />
                  <select value={sharePermission} onChange={(event) => setSharePermission(event.target.value)} className={inputClass}>
                    <option value="view">view</option>
                    <option value="edit">edit</option>
                  </select>
                  <Tooltip content="Share this dashboard with a team member">
                    <button
                      type="submit"
                      disabled={shareLoading}
                      className="rounded-full bg-amber-300 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-amber-200 disabled:cursor-not-allowed disabled:opacity-70"
                    >
                      {shareLoading ? 'Sharing...' : 'Share dashboard'}
                    </button>
                  </Tooltip>
                </form>
              </div>

              <div className="mt-5 grid gap-3 md:grid-cols-2">
                <div>
                  <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Recent Comments</p>
                  <ul className="mt-3 space-y-2 text-sm text-slate-200">
                    {comments.length === 0 ? <li className="text-slate-400">No comments yet.</li> : null}
                    {comments.map((item) => (
                      <li key={item.id} className="rounded-2xl border border-white/10 bg-white/5 p-3">
                        <p className="font-medium text-white">{item.user_email}</p>
                        <p className="mt-1 text-slate-400">{item.message}</p>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Recent Shares</p>
                  <ul className="mt-3 space-y-2 text-sm text-slate-200">
                    {shares.length === 0 ? <li className="text-slate-400">No shares yet.</li> : null}
                    {shares.map((item) => (
                      <li key={item.id} className="rounded-2xl border border-white/10 bg-white/5 p-3">
                        <p className="font-medium text-white">{item.target_email}</p>
                        <p className="mt-1 text-slate-400">Permission: {item.permission}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </section>

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
          </aside>
        </div>

        <footer className="mt-6 rounded-[1.5rem] border border-white/10 bg-slate-950/70 p-4 text-sm text-slate-300 backdrop-blur">
          <p>Status: {status}</p>
          {error ? <p className="mt-1 text-rose-300">Error: {error}</p> : null}
          <p className="mt-1 text-slate-400">API Base: {apiBase}</p>
        </footer>
      </section>
    </main>
      )}

      <GuidedTour
        isActive={tour.isTourActive}
        currentStep={tour.currentStep}
        currentStepIndex={tour.currentStepIndex}
        totalSteps={tour.totalSteps}
        onNext={tour.nextStep}
        onPrev={tour.prevStep}
        onSkip={tour.skipTour}
      />
    </>
  );
}

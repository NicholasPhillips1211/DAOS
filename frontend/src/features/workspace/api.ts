import {
  AutomationPlanRecord,
  ChartRecommendationRead,
  CommentRecord,
  DashboardRecord,
  ShareRecord,
  WorkspaceSummaryRead,
} from '../../types/domain';
import { assertOk, buildApiHeaders } from '../../lib/http';

/**
 * Persist a dashboard record from the workspace panel or query draft flow.
 */
export async function createDashboardRecord(
  apiBase: string,
  userEmail: string,
  payload: { workspace_id: number; name: string; description: string },
): Promise<DashboardRecord> {
  const response = await fetch(`${apiBase}/visualizations/dashboards`, {
    method: 'POST',
    headers: buildApiHeaders(userEmail),
    body: JSON.stringify(payload),
  });
  assertOk(response, 'Dashboard create failed');
  return (await response.json()) as DashboardRecord;
}

/**
 * Create a collaboration comment tied to the active workspace resource.
 */
export async function createCommentRecord(
  apiBase: string,
  userEmail: string,
  payload: {
    workspace_id: number;
    resource_type: string;
    resource_id: number;
    user_email: string;
    message: string;
  },
): Promise<CommentRecord> {
  const response = await fetch(`${apiBase}/collaboration/comments`, {
    method: 'POST',
    headers: buildApiHeaders(userEmail),
    body: JSON.stringify(payload),
  });
  assertOk(response, 'Comment failed');
  return (await response.json()) as CommentRecord;
}

/**
 * Share a resource with another workspace participant using role-style permissions.
 */
export async function createShareRecord(
  apiBase: string,
  userEmail: string,
  payload: {
    workspace_id: number;
    resource_type: string;
    resource_id: number;
    target_email: string;
    permission: string;
  },
): Promise<ShareRecord> {
  const response = await fetch(`${apiBase}/collaboration/shares`, {
    method: 'POST',
    headers: buildApiHeaders(userEmail),
    body: JSON.stringify(payload),
  });
  assertOk(response, 'Share failed');
  return (await response.json()) as ShareRecord;
}

/**
 * Ask the backend to generate an automation plan using local LLM or fallback logic.
 */
export async function generateAutomationPlan(
  apiBase: string,
  userEmail: string,
  payload: { workspace_id: number; objective: string },
): Promise<AutomationPlanRecord> {
  const response = await fetch(`${apiBase}/automation/generate`, {
    method: 'POST',
    headers: buildApiHeaders(userEmail),
    body: JSON.stringify(payload),
  });
  assertOk(response, 'Automation generation failed');
  return (await response.json()) as AutomationPlanRecord;
}

/**
 * Execute an existing automation plan by ID and return its refreshed state.
 */
export async function executeAutomationPlan(
  apiBase: string,
  userEmail: string,
  planId: number,
): Promise<AutomationPlanRecord> {
  const response = await fetch(`${apiBase}/automation/${planId}/execute`, {
    method: 'POST',
    headers: buildApiHeaders(userEmail),
  });
  assertOk(response, 'Automation execution failed');
  return (await response.json()) as AutomationPlanRecord;
}

/**
 * Request a chart recommendation for query output columns to guide dashboard defaults.
 */
export async function recommendChart(
  apiBase: string,
  userEmail: string,
  payload: { dataset_id: number; x_column: string; y_column: string | null; goal: string },
): Promise<ChartRecommendationRead | null> {
  const response = await fetch(`${apiBase}/visualizations/recommend-chart`, {
    method: 'POST',
    headers: buildApiHeaders(userEmail),
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    return null;
  }

  return (await response.json()) as ChartRecommendationRead;
}

/**
 * Fetch workspace summary signals so the UI can show onboarding guidance and recent context.
 */
export async function getWorkspaceSummary(
  apiBase: string,
  userEmail: string,
  workspaceId: number,
): Promise<WorkspaceSummaryRead> {
  const response = await fetch(`${apiBase}/workspaces/${workspaceId}/summary`, {
    headers: buildApiHeaders(userEmail, false),
  });
  assertOk(response, 'Workspace summary failed');
  return (await response.json()) as WorkspaceSummaryRead;
}

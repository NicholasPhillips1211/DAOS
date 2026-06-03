import { FormEvent, useRef, useState } from 'react';
import { createDashboardRecord, recommendChart } from '../api';
import { dashboardTemplates } from '../../dashboards/dashboardTemplates';
import type { ChartRecommendationRead, DashboardDraftPreview, DashboardRecord } from '../../../types/domain';
import type { WorkspaceWorkflowContext } from './workflowTypes';

export function useDashboardWorkflow({
  apiBase,
  commentEmail,
  setError,
  setStatus,
  workspaceIdNumber,
}: WorkspaceWorkflowContext) {
  const dashboardSectionRef = useRef<HTMLElement | null>(null);
  const [dashboardName, setDashboardName] = useState('Executive Overview');
  const [dashboardDescription, setDashboardDescription] = useState('Weekly KPI summary for leadership');
  const [selectedDashboardTemplate, setSelectedDashboardTemplate] = useState(dashboardTemplates[0].id);
  const [dashboards, setDashboards] = useState<DashboardRecord[]>([]);
  const [dashboardLoading, setDashboardLoading] = useState(false);

  function focusDashboardForm(): void {
    dashboardSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  async function createDashboard(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!validateWorkspaceId()) {
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
      rememberDashboard(record);
      setStatus(`Dashboard created: ${record.name}`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Failed to create dashboard');
    } finally {
      setDashboardLoading(false);
    }
  }

  function prepareDashboardFromDataset(name: string): void {
    setDashboardName(`${name} Overview`);
    setDashboardDescription(`Auto-prepared from dataset ${name}. Customize panels, then create dashboard.`);
    setStatus(`Dashboard draft prepared from dataset: ${name}`);
    focusDashboardForm();
  }

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

  async function createDashboardFromQueryBlueprint(payload: {
    datasetName: string;
    datasetId: number;
    columns: string[];
    rowCount: number;
    approvedDraft?: DashboardDraftPreview;
  }): Promise<void> {
    if (!validateWorkspaceId()) {
      throw new Error('Workspace ID must be a number.');
    }

    const draft = payload.approvedDraft ?? (await previewDashboardFromQueryBlueprint(payload));

    setError(null);
    setDashboardLoading(true);
    try {
      const record = await createDashboardRecord(apiBase, commentEmail, {
        workspace_id: workspaceIdNumber,
        name: draft.name,
        description: draft.description,
      });
      rememberDashboard(record);
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
      `Suggested starter panels: ${columnSummary}.` +
      recommendationLine;

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

  function rememberDashboard(record: DashboardRecord): void {
    setDashboards((previous) => [record, ...previous].slice(0, 6));
  }

  function validateWorkspaceId(): boolean {
    if (Number.isFinite(workspaceIdNumber)) {
      return true;
    }
    setError('Workspace ID must be a number.');
    return false;
  }

  return {
    applyDashboardTemplate,
    createDashboard,
    createDashboardFromQueryBlueprint,
    dashboardDescription,
    dashboardLoading,
    dashboardName,
    dashboardSectionRef,
    dashboards,
    prepareDashboardFromDataset,
    previewDashboardFromQueryBlueprint,
    selectedDashboardTemplate,
    setDashboardDescription,
    setDashboardName,
  };
}

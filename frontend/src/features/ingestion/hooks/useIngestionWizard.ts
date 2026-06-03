import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from 'react';
import { getWorkspaceSummary } from '../../workspace/api';
import { listWorkspaceDatasets, runDatasetSql, uploadDatasetFile } from '../api';
import { wizardStages } from '../constants';
import type { IngestionWizardProps, IngestionWizardState, PreviewSummary, WizardStage } from '../types';
import { buildSuggestedSql, parseCsvPreview } from '../utils';
import type { DashboardDraftPreview } from '../../../types/domain';

export function useIngestionWizard({
  apiBase,
  workspaceId,
  userEmail,
  onPrepareDashboard,
  onStatusChange,
  onPreviewDashboardFromQuery,
  onCreateDashboardFromQuery,
}: IngestionWizardProps) {
  const [datasetName, setDatasetName] = useState('Quarterly Sales Upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<PreviewSummary>({ headers: [], sampleRows: [] });
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<IngestionWizardState['uploadResult']>(null);
  const [datasets, setDatasets] = useState<IngestionWizardState['datasets']>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const [querySql, setQuerySql] = useState('');
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryResult, setQueryResult] = useState<IngestionWizardState['queryResult']>(null);
  const [draftPreviewLoading, setDraftPreviewLoading] = useState(false);
  const [dashboardDraftPreview, setDashboardDraftPreview] = useState<DashboardDraftPreview | null>(null);
  const [approvalChecked, setApprovalChecked] = useState(false);
  const [dashboardCreatingFromQuery, setDashboardCreatingFromQuery] = useState(false);
  const [workspaceSummary, setWorkspaceSummary] = useState<IngestionWizardState['workspaceSummary']>(null);
  const [loadingWorkspaceSummary, setLoadingWorkspaceSummary] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [loadingDatasets, setLoadingDatasets] = useState(false);

  const queryTemplate = useMemo(() => buildSuggestedSql(datasetName, preview.headers), [datasetName, preview.headers]);
  const activeDatasetId = selectedDatasetId ? Number(selectedDatasetId) : null;
  const currentStage = resolveCurrentStage({ dashboardDraftPreview, preview, queryResult, uploadResult });
  const currentStageIndex = wizardStages.findIndex((stage) => stage.id === currentStage);
  const nextStage = wizardStages[Math.min(currentStageIndex + 1, wizardStages.length - 1)];

  useEffect(() => {
    setQuerySql(queryTemplate);
  }, [queryTemplate]);

  useEffect(() => {
    let cancelled = false;

    async function loadWorkspaceSummary(): Promise<void> {
      setLoadingWorkspaceSummary(true);
      try {
        const summary = await getWorkspaceSummary(apiBase, userEmail, workspaceId);
        if (!cancelled) {
          setWorkspaceSummary(summary);
        }
      } catch {
        if (!cancelled) {
          setWorkspaceSummary(null);
        }
      } finally {
        if (!cancelled) {
          setLoadingWorkspaceSummary(false);
        }
      }
    }

    void loadWorkspaceSummary();

    return () => {
      cancelled = true;
    };
  }, [apiBase, userEmail, workspaceId]);

  useEffect(() => {
    let cancelled = false;

    async function loadDatasets(): Promise<void> {
      setLoadingDatasets(true);
      try {
        const items = await listWorkspaceDatasets(apiBase, userEmail, workspaceId);
        if (!cancelled) {
          setDatasets(items);
          if (items.length > 0) {
            setSelectedDatasetId(String(items[0].id));
          }
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : 'Failed to load datasets');
        }
      } finally {
        if (!cancelled) {
          setLoadingDatasets(false);
        }
      }
    }

    void loadDatasets();

    return () => {
      cancelled = true;
    };
  }, [apiBase, userEmail, workspaceId]);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>): Promise<void> {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setUploadResult(null);
    setError(null);
    setSuccessMessage(null);

    if (!file) {
      setPreview({ headers: [], sampleRows: [] });
      return;
    }

    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('Only CSV files are supported for the ingestion wizard.');
      setPreview({ headers: [], sampleRows: [] });
      return;
    }

    setPreview(parseCsvPreview(await file.text()));
    if (!datasetName.trim()) {
      setDatasetName(file.name.replace(/\.csv$/i, '').replace(/[-_]+/g, ' '));
    }
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!selectedFile) {
      setError('Choose a CSV file before uploading.');
      return;
    }
    if (!datasetName.trim()) {
      setError('Give the dataset a name before uploading.');
      return;
    }

    setError(null);
    setSuccessMessage(null);
    setUploading(true);

    try {
      const result = await uploadDatasetFile(apiBase, userEmail, {
        workspaceId,
        datasetName: datasetName.trim(),
        file: selectedFile,
      });
      setUploadResult(result);
      setSelectedDatasetId(String(result.dataset_id));
      setDatasets((previous) => [
        {
          id: result.dataset_id,
          workspace_id: result.workspace_id,
          name: result.dataset_name,
          source_type: 'file',
          state: result.state,
          storage_path: result.storage_path,
          created_at: result.created_at,
        },
        ...previous.filter((dataset) => dataset.id !== result.dataset_id),
      ].slice(0, 4));
      void getWorkspaceSummary(apiBase, userEmail, workspaceId).then(setWorkspaceSummary).catch(() => undefined);
      onPrepareDashboard?.(result.dataset_name);
      onStatusChange?.(`Dataset uploaded: ${result.dataset_name}`);
      setSuccessMessage(`Uploaded ${result.dataset_name} and generated profile results.`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Failed to upload dataset');
    } finally {
      setUploading(false);
    }
  }

  async function runQuery(): Promise<void> {
    if (!activeDatasetId) {
      setError('Select a dataset before running a query.');
      return;
    }
    if (!querySql.trim()) {
      setError('Query text is required.');
      return;
    }

    setError(null);
    setSuccessMessage(null);
    setQueryLoading(true);

    try {
      const result = await runDatasetSql(apiBase, userEmail, {
        datasetId: activeDatasetId,
        sql: querySql,
      });
      setQueryResult(result);
      setDashboardDraftPreview(null);
      setApprovalChecked(false);
      onStatusChange?.(`Query completed with ${result.row_count} row${result.row_count === 1 ? '' : 's'}`);
      setSuccessMessage(`Query completed with ${result.row_count} row${result.row_count === 1 ? '' : 's'} returned.`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Failed to run query');
    } finally {
      setQueryLoading(false);
    }
  }

  async function previewDashboardDraft(): Promise<void> {
    if (!queryResult || !activeDatasetId) {
      setError('Run a query first to preview a dashboard draft.');
      return;
    }
    if (!onPreviewDashboardFromQuery) {
      setError('Dashboard preview callback is not configured.');
      return;
    }

    const resolvedDatasetName = getResolvedDatasetName();

    setError(null);
    setSuccessMessage(null);
    setDraftPreviewLoading(true);
    try {
      const draftPreview = await onPreviewDashboardFromQuery({
        datasetName: resolvedDatasetName,
        datasetId: activeDatasetId,
        columns: queryResult.columns,
        rowCount: queryResult.row_count,
      });
      setDashboardDraftPreview(draftPreview);
      setApprovalChecked(false);
      onStatusChange?.('Dashboard draft preview ready for verification.');
      setSuccessMessage('Dashboard draft preview is ready for review.');
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Failed to preview dashboard draft');
    } finally {
      setDraftPreviewLoading(false);
    }
  }

  function updateDashboardDraftPreview(patch: Partial<DashboardDraftPreview>): void {
    setDashboardDraftPreview((current) => (current ? { ...current, ...patch } : current));
    setApprovalChecked(false);
  }

  async function createDashboardFromQuery(): Promise<void> {
    if (!queryResult || !activeDatasetId) {
      setError('Run a query first to create a dashboard from its result.');
      return;
    }
    if (!dashboardDraftPreview) {
      setError('Generate and verify a dashboard draft preview before approval.');
      return;
    }
    if (!approvalChecked) {
      setError('Confirm draft verification before approving dashboard creation.');
      return;
    }
    if (!onCreateDashboardFromQuery) {
      setError('Dashboard creation callback is not configured.');
      return;
    }

    const resolvedDatasetName = getResolvedDatasetName();

    setError(null);
    setSuccessMessage(null);
    setDashboardCreatingFromQuery(true);
    try {
      await Promise.resolve(
        onCreateDashboardFromQuery({
          datasetName: resolvedDatasetName,
          datasetId: activeDatasetId,
          columns: queryResult.columns,
          rowCount: queryResult.row_count,
          approvedDraft: dashboardDraftPreview,
        }),
      );
      onStatusChange?.(`Dashboard created from query result for ${resolvedDatasetName}`);
      setSuccessMessage(`Dashboard created from query result for ${resolvedDatasetName}.`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Failed to create dashboard from query');
    } finally {
      setDashboardCreatingFromQuery(false);
    }
  }

  function getResolvedDatasetName(): string {
    const selectedDataset = datasets.find((dataset) => dataset.id === activeDatasetId);
    return selectedDataset?.name ?? uploadResult?.dataset_name ?? datasetName;
  }

  const state: IngestionWizardState = {
    activeDatasetId,
    approvalChecked,
    canUpload: Boolean(selectedFile && datasetName.trim()),
    currentStage,
    currentStageIndex,
    dashboardCreatingFromQuery,
    dashboardDraftPreview,
    datasetName,
    datasets,
    draftPreviewLoading,
    error,
    loadingDatasets,
    loadingWorkspaceSummary,
    nextStage,
    preview,
    progressPercent: ((currentStageIndex + 1) / wizardStages.length) * 100,
    queryLoading,
    queryResult,
    querySql,
    queryTemplate,
    selectedDatasetId,
    selectedFile,
    successMessage,
    uploadResult,
    uploading,
    workspaceId,
    workspaceSummary,
  };

  return {
    ...state,
    createDashboardFromQuery,
    handleFileChange,
    handleUpload,
    onPrepareDashboard,
    previewDashboardDraft,
    runQuery,
    setApprovalChecked,
    setDatasetName,
    setQuerySql,
    setSelectedDatasetId,
    updateDashboardDraftPreview,
  };
}

function resolveCurrentStage({
  dashboardDraftPreview,
  preview,
  queryResult,
  uploadResult,
}: Pick<IngestionWizardState, 'dashboardDraftPreview' | 'preview' | 'queryResult' | 'uploadResult'>): WizardStage {
  if (dashboardDraftPreview) {
    return 'dashboard';
  }
  if (queryResult) {
    return 'query';
  }
  if (uploadResult) {
    return 'upload';
  }
  return preview.headers.length > 0 ? 'preview' : 'choose';
}

export type IngestionWizardViewModel = ReturnType<typeof useIngestionWizard>;

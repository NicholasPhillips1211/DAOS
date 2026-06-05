import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import { getWorkspaceSummary } from '../../workspace/api';
import { getIngestionJob, listWorkspaceDatasets, runDatasetSql, uploadDatasetFile } from '../api';
import { wizardStages } from '../constants';
import type { IngestionWizardProps, IngestionWizardState, PreviewSummary, WizardStage } from '../types';
import { buildSuggestedSql, parseCsvPreview } from '../utils';
import type { DashboardDraftPreview } from '../../../types/domain';

const MAX_UPLOAD_POLL_ATTEMPTS = 60;
const UPLOAD_POLL_DELAYS_MS = [1000, 1500, 2500, 4000, 5000];

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
  const uploadPollToken = useRef(0);

  const queryTemplate = useMemo(() => buildSuggestedSql(datasetName, preview.headers), [datasetName, preview.headers]);
  const activeDatasetId = selectedDatasetId ? Number(selectedDatasetId) : null;
  const currentStage = resolveCurrentStage({ dashboardDraftPreview, preview, queryResult, uploadResult });
  const currentStageIndex = wizardStages.findIndex((stage) => stage.id === currentStage);
  const nextStage = wizardStages[Math.min(currentStageIndex + 1, wizardStages.length - 1)];

  useEffect(() => {
    setQuerySql(queryTemplate);
  }, [queryTemplate]);

  useEffect(() => {
    return () => {
      uploadPollToken.current += 1;
    };
  }, []);

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
    uploadPollToken.current += 1;
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
      onStatusChange?.(`Upload accepted: ${result.dataset_name}`);
      setSuccessMessage(`Upload accepted. Profiling is ${result.current_step ?? result.status}.`);
      const pollToken = uploadPollToken.current + 1;
      uploadPollToken.current = pollToken;
      void pollUploadJob(result, pollToken);
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

  async function pollUploadJob(initialResult: IngestionWizardState['uploadResult'], pollToken: number): Promise<void> {
    if (!initialResult) {
      return;
    }

    let latestResult = initialResult;
    for (let attempt = 0; attempt < MAX_UPLOAD_POLL_ATTEMPTS; attempt += 1) {
      await delay(getUploadPollDelay(attempt));
      if (!isCurrentUploadPoll(pollToken)) {
        return;
      }
      try {
        const job = await getIngestionJob(apiBase, userEmail, latestResult.job_id);
        if (!isCurrentUploadPoll(pollToken)) {
          return;
        }
        latestResult = {
          ...latestResult,
          dataset_id: job.dataset_id,
          dataset_name: job.dataset_name ?? latestResult.dataset_name,
          status: job.status,
          current_step: job.current_step,
          progress_percent: job.progress_percent,
          quality_score: job.quality_score,
          row_count: job.row_count,
          rejected_rows: job.rejected_rows,
          storage_path: job.storage_path,
          error_message: job.error_message,
          started_at: job.started_at,
          finished_at: job.finished_at,
        };
        setUploadResult(latestResult);

        if (job.status === 'completed' && job.dataset_id) {
          const refreshedDatasets = await listWorkspaceDatasets(apiBase, userEmail, workspaceId);
          if (!isCurrentUploadPoll(pollToken)) {
            return;
          }
          setDatasets(refreshedDatasets);
          setSelectedDatasetId(String(job.dataset_id));
          void getWorkspaceSummary(apiBase, userEmail, workspaceId)
            .then((summary) => {
              if (isCurrentUploadPoll(pollToken)) {
                setWorkspaceSummary(summary);
              }
            })
            .catch(() => undefined);
          onPrepareDashboard?.(latestResult.dataset_name);
          onStatusChange?.(`Dataset profiled: ${latestResult.dataset_name}`);
          setSuccessMessage(`Profile complete for ${latestResult.dataset_name}.`);
          return;
        }

        if (job.status === 'failed') {
          setError(job.error_message ?? 'Ingestion job failed');
          return;
        }
      } catch (requestError) {
        if (isCurrentUploadPoll(pollToken)) {
          setError(requestError instanceof Error ? requestError.message : 'Failed to refresh ingestion job');
        }
        return;
      }
    }

    if (isCurrentUploadPoll(pollToken)) {
      setSuccessMessage('Upload is still processing. Refresh the job list for the latest state.');
    }
  }

  function isCurrentUploadPoll(pollToken: number): boolean {
    return uploadPollToken.current === pollToken;
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

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function getUploadPollDelay(attempt: number): number {
  return UPLOAD_POLL_DELAYS_MS[Math.min(attempt, UPLOAD_POLL_DELAYS_MS.length - 1)];
}

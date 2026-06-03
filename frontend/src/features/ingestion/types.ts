import type {
  DashboardDraftPreview,
  DatasetRecord,
  IngestionUploadRead,
  QueryResult,
  WorkspaceSummaryRead,
} from '../../types/domain';

export type IngestionWizardProps = {
  apiBase: string;
  workspaceId: number;
  userEmail: string;
  onPrepareDashboard?: (datasetName: string) => void;
  onStatusChange?: (message: string) => void;
  onPreviewDashboardFromQuery?: (payload: {
    datasetName: string;
    datasetId: number;
    columns: string[];
    rowCount: number;
  }) => Promise<DashboardDraftPreview>;
  onCreateDashboardFromQuery?: (payload: {
    datasetName: string;
    datasetId: number;
    columns: string[];
    rowCount: number;
    approvedDraft?: DashboardDraftPreview;
  }) => Promise<void> | void;
};

export type PreviewSummary = {
  headers: string[];
  sampleRows: string[][];
};

export type WizardStage = 'choose' | 'preview' | 'upload' | 'query' | 'dashboard';

export type WizardStageConfig = {
  id: WizardStage;
  label: string;
  detail: string;
};

export type IngestionWizardState = {
  activeDatasetId: number | null;
  approvalChecked: boolean;
  canUpload: boolean;
  currentStage: WizardStage;
  currentStageIndex: number;
  dashboardCreatingFromQuery: boolean;
  dashboardDraftPreview: DashboardDraftPreview | null;
  datasetName: string;
  datasets: DatasetRecord[];
  draftPreviewLoading: boolean;
  error: string | null;
  loadingDatasets: boolean;
  loadingWorkspaceSummary: boolean;
  nextStage: WizardStageConfig;
  preview: PreviewSummary;
  progressPercent: number;
  queryLoading: boolean;
  queryResult: QueryResult | null;
  querySql: string;
  queryTemplate: string;
  selectedDatasetId: string;
  selectedFile: File | null;
  successMessage: string | null;
  uploadResult: IngestionUploadRead | null;
  uploading: boolean;
  workspaceId: number;
  workspaceSummary: WorkspaceSummaryRead | null;
};

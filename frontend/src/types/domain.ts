export type DashboardRecord = {
  id: number;
  workspace_id: number;
  name: string;
  description?: string | null;
};

export type DashboardDraftPreview = {
  name: string;
  description: string;
  recommendation?: {
    chartType: string;
    reason: string;
    bestPractices: string[];
  };
};

export type ChartRecommendationRead = {
  chart_type: string;
  reason: string;
  best_practices: string[];
};

export type CommentRecord = {
  id: number;
  workspace_id: number;
  resource_type: string;
  resource_id: number;
  user_email: string;
  message: string;
};

export type ShareRecord = {
  id: number;
  workspace_id: number;
  resource_type: string;
  resource_id: number;
  target_email: string;
  permission: string;
};

export type AutomationPlanRecord = {
  id: number;
  workspace_id: number;
  objective: string;
  provider: string;
  model_name?: string | null;
  status: string;
  summary: string;
  automation_json: string;
  created_at: string;
  execution_status?: string | null;
  executed_at?: string | null;
  execution_results_json?: string | null;
};

export type AutomationPlanPayload = {
  title: string;
  summary: string;
  automation_score: number;
  signals?: Record<string, number>;
  triggers: Array<{ name: string; description: string }>;
  actions: Array<{ name: string; description: string }>;
  next_steps: string[];
  provider_notes?: string;
};

export type DatasetRecord = {
  id: number;
  workspace_id: number;
  name: string;
  source_type: string;
  state: string;
  storage_path?: string | null;
  created_at: string;
};

export type WorkspaceDatasetSummary = {
  id: number;
  name: string;
  source_type: string;
  state: string;
  created_at: string;
};

export type WorkspaceSummaryRead = {
  workspace_id: number;
  workspace_name: string;
  workspace_description?: string | null;
  dataset_count: number;
  membership_count: number;
  has_datasets: boolean;
  recommended_next_action: string;
  recent_datasets: WorkspaceDatasetSummary[];
  latest_dataset?: WorkspaceDatasetSummary | null;
};

export type IngestionUploadRead = {
  job_id: number;
  work_item_id?: number | null;
  dataset_id?: number | null;
  workspace_id: number;
  dataset_name: string;
  state?: string | null;
  status: string;
  current_step?: string | null;
  progress_percent?: number;
  quality_score: number;
  row_count: number;
  rejected_rows: number;
  storage_path?: string | null;
  report_id?: number | null;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
};

export type IngestionJobRead = {
  id: number;
  workspace_id: number;
  dataset_id?: number | null;
  work_item_id?: number | null;
  dataset_name?: string | null;
  source_name: string;
  source_type: string;
  storage_path?: string | null;
  status: string;
  current_step?: string | null;
  progress_percent?: number;
  row_count: number;
  rejected_rows: number;
  quality_score: number;
  error_message?: string | null;
  actor?: string | null;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
};

export type DataQualityColumnSummary = {
  name: string;
  missing: number;
  sample_size: number;
  inferred_type: string;
};

export type DataCleaningSummary = {
  raw_row_count: number;
  cleaned_row_count: number;
  blank_rows_removed: number;
  duplicate_rows_removed: number;
  cells_trimmed: number;
  rejected_row_count: number;
  extra_columns_preserved?: number;
  short_rows_padded?: number;
  engine?: string;
  policy?: {
    id: string;
    version: string;
    engine: string;
    rules: string[];
  };
  policy_fingerprint?: string;
  artifact_fingerprints?: {
    raw?: string;
    cleaned?: string;
    rejected?: string;
    policy?: string;
  };
  headers_normalized: Array<{ from: string; to: string }>;
  rules: string[];
  cleaned_path: string;
  rejected_path?: string;
};

export type DataQualityDelta = {
  raw_quality_score: number;
  cleaned_quality_score: number;
  score_delta: number;
  raw_row_count: number;
  cleaned_row_count: number;
  rejected_row_count: number;
  blank_rows_removed: number;
  duplicate_rows_removed: number;
};

export type DataQualityReportRead = {
  id: number;
  dataset_id: number;
  row_count: number;
  rejected_rows: number;
  quality_score: number;
  columns: DataQualityColumnSummary[];
  issues: string[];
  metadata?: {
    profile_version?: string;
    raw_storage_path?: string;
    cleaned_storage_path?: string;
    rejected_storage_path?: string;
    cleaning?: DataCleaningSummary;
    quality_delta?: DataQualityDelta;
    [key: string]: unknown;
  } | null;
  created_at: string;
};

export type QueryResult = {
  columns: string[];
  rows: Array<Record<string, unknown>>;
  row_count: number;
};

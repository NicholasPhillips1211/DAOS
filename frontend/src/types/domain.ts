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
  dataset_id: number;
  workspace_id: number;
  dataset_name: string;
  state: string;
  quality_score: number;
  row_count: number;
  rejected_rows: number;
  storage_path: string;
  report_id: number;
  created_at: string;
};

export type QueryResult = {
  columns: string[];
  rows: Array<Record<string, unknown>>;
  row_count: number;
};

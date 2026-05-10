import { DatasetRecord, IngestionUploadRead, QueryResult } from '../../types/domain';
import { assertOk, buildApiHeaders } from '../../lib/http';

/**
 * Fetch datasets and keep only the current workspace scope for quick selection UIs.
 */
export async function listWorkspaceDatasets(
  apiBase: string,
  userEmail: string,
  workspaceId: number,
): Promise<DatasetRecord[]> {
  const response = await fetch(`${apiBase}/datasets`, {
    headers: buildApiHeaders(userEmail, false),
  });
  assertOk(response, 'Dataset list failed');
  const items = (await response.json()) as DatasetRecord[];
  return items.filter((item) => item.workspace_id === workspaceId).slice(0, 4);
}

/**
 * Upload CSV content and trigger profiling so the UI can continue into query/dashboards.
 */
export async function uploadDatasetFile(
  apiBase: string,
  userEmail: string,
  payload: { workspaceId: number; datasetName: string; file: File },
): Promise<IngestionUploadRead> {
  const formData = new FormData();
  formData.append('workspace_id', String(payload.workspaceId));
  formData.append('dataset_name', payload.datasetName);
  formData.append('file', payload.file);

  const response = await fetch(`${apiBase}/ingestion/upload`, {
    method: 'POST',
    headers: buildApiHeaders(userEmail, false),
    body: formData,
  });
  assertOk(response, 'Upload failed');
  return (await response.json()) as IngestionUploadRead;
}

/**
 * Run SQL against the dataset virtual table and return tabular output for preview/drafts.
 */
export async function runDatasetSql(
  apiBase: string,
  userEmail: string,
  payload: { datasetId: number; sql: string },
): Promise<QueryResult> {
  const response = await fetch(`${apiBase}/datasets/${payload.datasetId}/query`, {
    method: 'POST',
    headers: buildApiHeaders(userEmail),
    body: JSON.stringify({ sql: payload.sql }),
  });
  assertOk(response, 'Query failed');
  return (await response.json()) as QueryResult;
}

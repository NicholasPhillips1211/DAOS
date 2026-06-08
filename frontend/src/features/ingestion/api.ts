import {
  DataQualityReportRead,
  DatasetRecord,
  IngestionJobRead,
  IngestionUploadRead,
  QueryResult,
} from '../../types/domain';
import { assertOk, buildApiHeaders } from '../../lib/http';

/**
 * Fetch datasets and keep only the current workspace scope for quick selection UIs.
 */
export async function listWorkspaceDatasets(
  apiBase: string,
  userEmail: string,
  workspaceId: number,
): Promise<DatasetRecord[]> {
  const response = await fetch(`${apiBase}/datasets?workspace_id=${workspaceId}`, {
    headers: buildApiHeaders(userEmail, false),
  });
  assertOk(response, 'Dataset list failed');
  const items = (await response.json()) as DatasetRecord[];
  return items.slice(0, 4);
}

/**
 * Upload CSV content and trigger cleaning/profiling so the UI can continue into query/dashboards.
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
 * Fetch the durable ingestion job so the UI can follow async cleaning/profiling.
 */
export async function getIngestionJob(
  apiBase: string,
  userEmail: string,
  jobId: number,
): Promise<IngestionJobRead> {
  const response = await fetch(`${apiBase}/ingestion/jobs/${jobId}`, {
    headers: buildApiHeaders(userEmail, false),
  });
  assertOk(response, 'Ingestion job lookup failed');
  return (await response.json()) as IngestionJobRead;
}

/**
 * Fetch the stored quality report so analysts can see cleaning and profiling evidence.
 */
export async function getDatasetQualityReport(
  apiBase: string,
  userEmail: string,
  datasetId: number,
): Promise<DataQualityReportRead> {
  const response = await fetch(`${apiBase}/datasets/${datasetId}/quality`, {
    headers: buildApiHeaders(userEmail, false),
  });
  assertOk(response, 'Quality report lookup failed');
  return (await response.json()) as DataQualityReportRead;
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

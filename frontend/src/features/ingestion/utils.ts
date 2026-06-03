import type { PreviewSummary } from './types';

export function parseCsvPreview(text: string, limit = 5): PreviewSummary {
  const lines = text
    .replace(/^\uFEFF/, '')
    .split(/\r?\n/)
    .map((line) => line.trimEnd())
    .filter((line) => line.length > 0);

  if (lines.length === 0) {
    return { headers: [], sampleRows: [] };
  }

  const rows = lines.map((line) =>
    line
      .split(',')
      .map((value) => value.trim())
      .map((value) => value.replace(/^"|"$/g, '')),
  );

  return {
    headers: rows[0] ?? [],
    sampleRows: rows.slice(1, limit + 1),
  };
}

export function buildSuggestedSql(datasetName: string, headers: string[]): string {
  const title = datasetName.trim() || 'uploaded dataset';
  const selectedColumns = headers
    .slice(0, 5)
    .map((header) => `"${header}"`)
    .join(', ');

  return headers.length > 0
    ? `-- ${title}
SELECT ${selectedColumns}
FROM dataset
ORDER BY 1 DESC
LIMIT 25;`
    : `-- ${title}
SELECT *
FROM dataset
LIMIT 25;`;
}

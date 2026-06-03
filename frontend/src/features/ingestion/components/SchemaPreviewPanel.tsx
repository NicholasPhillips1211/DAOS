import { WorkflowState } from '../../../components/ui';
import type { PreviewSummary } from '../types';

type SchemaPreviewPanelProps = {
  preview: PreviewSummary;
};

export function SchemaPreviewPanel({ preview }: SchemaPreviewPanelProps) {
  if (preview.headers.length === 0) {
    return (
      <WorkflowState
        variant="empty"
        title="Preview the file first"
        description="Choose a CSV to generate a schema preview and sample rows before uploading the dataset."
      />
    );
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm uppercase tracking-[0.25em] text-slate-300">Schema preview</h3>
        <span className="rounded-full border border-white/10 bg-slate-950/60 px-3 py-1 text-xs text-slate-300">
          {preview.headers.length} columns
        </span>
      </div>
      <div className="mt-4 overflow-hidden rounded-xl border border-white/10">
        <table className="w-full border-collapse text-left text-sm text-slate-200">
          <thead className="bg-slate-950/70 text-xs uppercase tracking-[0.2em] text-slate-400">
            <tr>
              {preview.headers.map((header) => (
                <th key={header} className="px-3 py-2 font-medium">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {preview.sampleRows.length > 0 ? (
              preview.sampleRows.map((row, rowIndex) => (
                <tr key={`${rowIndex}-${row.join('-')}`} className={rowIndex % 2 === 0 ? 'bg-white/5' : 'bg-transparent'}>
                  {preview.headers.map((_, columnIndex) => (
                    <td key={`${rowIndex}-${columnIndex}`} className="px-3 py-2 text-slate-300">
                      {row[columnIndex] ?? 'No value'}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td className="px-3 py-4 text-slate-400" colSpan={preview.headers.length}>
                  The file has headers but no data rows to preview.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

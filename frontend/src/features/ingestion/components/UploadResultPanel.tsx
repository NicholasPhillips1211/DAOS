import { WorkflowState } from '../../../components/ui';
import { wizardStages } from '../constants';
import type { IngestionWizardViewModel } from '../hooks/useIngestionWizard';

type UploadResultPanelProps = {
  wizard: IngestionWizardViewModel;
};

export function UploadResultPanel({ wizard }: UploadResultPanelProps) {
  const uploadStatus = wizard.uploadResult?.status;
  const uploadComplete = uploadStatus === 'completed';
  const uploadFailed = uploadStatus === 'failed';
  const statusLabel = uploadComplete ? 'Ready for analysis' : uploadFailed ? 'Needs attention' : 'Profiling queued';

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm uppercase tracking-[0.25em] text-slate-300">Upload result</h3>
        <span className="rounded-full border border-white/10 bg-slate-950/60 px-3 py-1 text-xs text-slate-300">
          {wizard.uploadResult ? statusLabel : 'Waiting for upload'}
        </span>
      </div>
      {wizard.uploadResult ? (
        <div className="mt-4 space-y-3 text-sm text-slate-200">
          <div className="rounded-xl border border-emerald-300/20 bg-emerald-400/10 p-3">
            <p className="font-medium text-emerald-100">
              {uploadComplete
                ? `${wizard.uploadResult.dataset_name} profile complete`
                : `${wizard.uploadResult.dataset_name} accepted for processing`}
            </p>
            <p className="mt-1 text-emerald-50/80">
              Quality score: {wizard.uploadResult.quality_score}% - {wizard.uploadResult.row_count} rows -{' '}
              {wizard.uploadResult.rejected_rows} rejected
            </p>
            <p className="mt-1 text-xs uppercase tracking-[0.2em] text-emerald-50/70">
              Job #{wizard.uploadResult.job_id} - {wizard.uploadResult.status}
              {wizard.uploadResult.current_step ? ` - ${wizard.uploadResult.current_step}` : ''}
            </p>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-950/70">
              <div
                className="h-full rounded-full bg-emerald-300"
                style={{ width: `${wizard.uploadResult.progress_percent ?? 0}%` }}
              />
            </div>
          </div>
          <div className="rounded-xl border border-white/10 bg-slate-950/60 p-3 text-slate-300">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Next move</p>
            <p className="mt-2 leading-6">
              {uploadComplete
                ? 'Use the query template above, then create a dashboard from the profiled dataset.'
                : 'Keep this panel open while the worker profiles the file and prepares the dataset for analysis.'}
            </p>
          </div>
        </div>
      ) : (
        <div className="mt-4">
          <WorkflowState
            variant="info"
            title="Waiting for an upload"
            description="Upload a CSV to see row counts, quality score, and storage details here."
            action={
              <p className="text-xs uppercase tracking-[0.2em] text-amber-50/80">
                Current stage: {wizardStages[wizard.currentStageIndex]?.label}
              </p>
            }
          />
        </div>
      )}
    </div>
  );
}

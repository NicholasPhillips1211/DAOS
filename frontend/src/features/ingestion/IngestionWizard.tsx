import { cardClass, WorkflowState } from '../../components/ui';
import { DatasetQueryPanel } from './components/DatasetQueryPanel';
import { IngestionWizardHeader } from './components/IngestionWizardHeader';
import { QueryBuilderPanel } from './components/QueryBuilderPanel';
import { QueryResultPanel } from './components/QueryResultPanel';
import { SchemaPreviewPanel } from './components/SchemaPreviewPanel';
import { SourceSetupPanel } from './components/SourceSetupPanel';
import { UploadControls } from './components/UploadControls';
import { UploadResultPanel } from './components/UploadResultPanel';
import { WorkflowProgressPanel } from './components/WorkflowProgressPanel';
import { WorkspaceSummaryPanel } from './components/WorkspaceSummaryPanel';
import { useIngestionWizard } from './hooks/useIngestionWizard';
import type { IngestionWizardProps } from './types';

export function IngestionWizard(props: IngestionWizardProps) {
  const wizard = useIngestionWizard(props);

  return (
    <section className={cardClass}>
      <IngestionWizardHeader wizard={wizard} />

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        {wizard.successMessage ? (
          <div className="xl:col-span-2">
            <WorkflowState variant="success" title="Step complete" description={wizard.successMessage} />
          </div>
        ) : null}

        <form className="space-y-5" onSubmit={wizard.handleUpload}>
          <WorkflowProgressPanel wizard={wizard} />
          <WorkspaceSummaryPanel wizard={wizard} />
          <SourceSetupPanel wizard={wizard} />
          <SchemaPreviewPanel preview={wizard.preview} />
          <QueryBuilderPanel wizard={wizard} />
          <UploadControls wizard={wizard} />
        </form>

        <div className="space-y-6">
          <DatasetQueryPanel wizard={wizard} />
          <UploadResultPanel wizard={wizard} />
          <QueryResultPanel wizard={wizard} />
        </div>
      </div>

      {wizard.error ? (
        <div className="mt-4">
          <WorkflowState variant="error" title="Workflow error" description={wizard.error} />
        </div>
      ) : null}
    </section>
  );
}

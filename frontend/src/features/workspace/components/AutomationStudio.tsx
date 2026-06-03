import { AutomationExecutionPanel } from './automation/AutomationExecutionPanel';
import { AutomationPlanSummary } from './automation/AutomationPlanSummary';
import { AutomationRecipePanel } from './automation/AutomationRecipePanel';
import { AutomationSignalsPanel } from './automation/AutomationSignalsPanel';
import { AutomationStudioHeader } from './automation/AutomationStudioHeader';
import type { WorkspaceWorkflow } from '../hooks/useWorkspaceWorkflow';

type AutomationStudioProps = {
  workflow: WorkspaceWorkflow;
};

export function AutomationStudio({ workflow }: AutomationStudioProps) {
  return (
    <>
      <AutomationStudioHeader workflow={workflow} />
      <div className="grid gap-4 lg:grid-cols-2">
        <AutomationPlanSummary workflow={workflow} />
        <AutomationSignalsPanel workflow={workflow} />
      </div>
      <AutomationRecipePanel parsedAutomation={workflow.parsedAutomation} />
      <AutomationExecutionPanel workflow={workflow} />
    </>
  );
}

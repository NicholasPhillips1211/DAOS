import { FormEvent, useMemo, useState } from 'react';
import { executeAutomationPlan, generateAutomationPlan } from '../api';
import type { AutomationPlanPayload, AutomationPlanRecord } from '../../../types/domain';
import type { WorkspaceWorkflowContext } from './workflowTypes';

function parseAutomationPayload(value: string): AutomationPlanPayload | null {
  try {
    return JSON.parse(value) as AutomationPlanPayload;
  } catch {
    return null;
  }
}

export function useAutomationWorkflow({
  apiBase,
  commentEmail,
  setError,
  setStatus,
  workspaceIdNumber,
}: WorkspaceWorkflowContext) {
  const [automationObjective, setAutomationObjective] = useState(
    'Automate daily workspace triage, dashboard refreshes, and stakeholder updates',
  );
  const [automationPlans, setAutomationPlans] = useState<AutomationPlanRecord[]>([]);
  const [automationLoading, setAutomationLoading] = useState(false);
  const [automationExecuting, setAutomationExecuting] = useState(false);

  const latestAutomationPlan = automationPlans[0];
  const parsedAutomation = useMemo(
    () => (latestAutomationPlan ? parseAutomationPayload(latestAutomationPlan.automation_json) : null),
    [latestAutomationPlan],
  );

  async function generateAutomation(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!validateWorkspaceId()) {
      return;
    }

    setError(null);
    setAutomationLoading(true);
    try {
      const record = await generateAutomationPlan(apiBase, commentEmail, {
        workspace_id: workspaceIdNumber,
        objective: automationObjective,
      });
      setAutomationPlans((previous) => [record, ...previous].slice(0, 6));
      setStatus(`Automation generated via ${record.provider}`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Failed to generate automation plan');
    } finally {
      setAutomationLoading(false);
    }
  }

  async function executeAutomation(): Promise<void> {
    if (!latestAutomationPlan) {
      setError('No automation plan to execute.');
      return;
    }

    setError(null);
    setAutomationExecuting(true);
    try {
      const updated = await executeAutomationPlan(apiBase, commentEmail, latestAutomationPlan.id);
      setAutomationPlans((previous) => previous.map((plan) => (plan.id === updated.id ? updated : plan)));
      setStatus(`Automation executed successfully at ${updated.executed_at}`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Failed to execute automation plan');
    } finally {
      setAutomationExecuting(false);
    }
  }

  function validateWorkspaceId(): boolean {
    if (Number.isFinite(workspaceIdNumber)) {
      return true;
    }
    setError('Workspace ID must be a number.');
    return false;
  }

  return {
    automationExecuting,
    automationLoading,
    automationObjective,
    automationPlans,
    executeAutomation,
    generateAutomation,
    latestAutomationPlan,
    parsedAutomation,
    setAutomationObjective,
  };
}

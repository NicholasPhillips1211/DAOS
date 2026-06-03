import { useMemo, useState } from 'react';
import { apiBase } from '../../../services/apiConfig';
import { useAutomationWorkflow } from './useAutomationWorkflow';
import { useCollaborationWorkflow } from './useCollaborationWorkflow';
import { useDashboardWorkflow } from './useDashboardWorkflow';

export function useWorkspaceWorkflow() {
  const [workspaceId, setWorkspaceId] = useState('1');
  const [commentEmail, setCommentEmail] = useState('analyst@daos.local');
  const [status, setStatus] = useState('Ready');
  const [error, setError] = useState<string | null>(null);

  const workspaceIdNumber = useMemo(() => Number(workspaceId), [workspaceId]);
  const context = { apiBase, commentEmail, setError, setStatus, workspaceIdNumber };
  const dashboard = useDashboardWorkflow(context);
  const collaboration = useCollaborationWorkflow({ ...context, dashboards: dashboard.dashboards });
  const automation = useAutomationWorkflow(context);

  const workspaceSignals = {
    dashboards: dashboard.dashboards.length,
    comments: collaboration.comments.length,
    shares: collaboration.shares.length,
    automations: automation.automationPlans.length,
  };

  return {
    ...automation,
    ...collaboration,
    ...dashboard,
    apiBase,
    commentEmail,
    error,
    setCommentEmail,
    setError,
    setStatus,
    setWorkspaceId,
    status,
    workspaceId,
    workspaceIdNumber,
    workspaceSignals,
  };
}

export type WorkspaceWorkflow = ReturnType<typeof useWorkspaceWorkflow>;

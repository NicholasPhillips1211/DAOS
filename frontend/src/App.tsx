import { FormEvent, useMemo, useState } from 'react';

type DashboardRecord = {
  id: number;
  workspace_id: number;
  name: string;
  description?: string | null;
};

type CommentRecord = {
  id: number;
  workspace_id: number;
  resource_type: string;
  resource_id: number;
  user_email: string;
  message: string;
};

type ShareRecord = {
  id: number;
  workspace_id: number;
  resource_type: string;
  resource_id: number;
  target_email: string;
  permission: string;
};

const apiBase = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export default function App() {
  const [workspaceId, setWorkspaceId] = useState('1');
  const [dashboardName, setDashboardName] = useState('Executive Overview');
  const [dashboardDescription, setDashboardDescription] = useState('Weekly KPI summary for leadership');
  const [dashboards, setDashboards] = useState<DashboardRecord[]>([]);

  const [commentEmail, setCommentEmail] = useState('analyst@daos.local');
  const [commentMessage, setCommentMessage] = useState('Revenue panel should include a MoM trend.');
  const [comments, setComments] = useState<CommentRecord[]>([]);

  const [shareEmail, setShareEmail] = useState('stakeholder@daos.local');
  const [sharePermission, setSharePermission] = useState('view');
  const [shares, setShares] = useState<ShareRecord[]>([]);

  const [status, setStatus] = useState('Ready');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const workspaceIdNumber = useMemo(() => Number(workspaceId), [workspaceId]);

  // Keep dashboard creation local to the page so new records appear immediately in the UI.
  async function createDashboard(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const response = await fetch(`${apiBase}/visualizations/dashboards`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workspace_id: workspaceIdNumber,
          name: dashboardName,
          description: dashboardDescription,
        }),
      });
      if (!response.ok) {
        throw new Error(`Dashboard create failed (${response.status})`);
      }
      const record = (await response.json()) as DashboardRecord;
      setDashboards((previous) => [record, ...previous].slice(0, 10));
      setStatus(`Dashboard created: ${record.name}`);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Failed to create dashboard';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  // Comments are routed through the backend so they are persisted and audited.
  async function postComment(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const latestDashboard = dashboards[0];
      const response = await fetch(`${apiBase}/collaboration/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workspace_id: workspaceIdNumber,
          resource_type: 'dashboard',
          resource_id: latestDashboard?.id ?? 1,
          user_email: commentEmail,
          message: commentMessage,
        }),
      });
      if (!response.ok) {
        throw new Error(`Comment failed (${response.status})`);
      }
      const record = (await response.json()) as CommentRecord;
      setComments((previous) => [record, ...previous].slice(0, 10));
      setStatus(`Comment added by ${record.user_email}`);
      setCommentMessage('');
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Failed to post comment';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  // Shares use the same backend workspace model so access control stays server-side.
  async function createShare(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const latestDashboard = dashboards[0];
      const response = await fetch(`${apiBase}/collaboration/shares`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workspace_id: workspaceIdNumber,
          resource_type: 'dashboard',
          resource_id: latestDashboard?.id ?? 1,
          target_email: shareEmail,
          permission: sharePermission,
        }),
      });
      if (!response.ok) {
        throw new Error(`Share failed (${response.status})`);
      }
      const record = (await response.json()) as ShareRecord;
      setShares((previous) => [record, ...previous].slice(0, 10));
      setStatus(`Shared dashboard with ${record.target_email}`);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Failed to create share';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen text-slate-100">
      <section className="mx-auto w-full max-w-7xl px-6 py-8 lg:px-12">
        <header className="mb-8 flex flex-col gap-4 rounded-3xl border border-cyan-200/20 bg-black/30 p-6 backdrop-blur md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.45em] text-cyan-200/90">DAOS Collaborate</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">Dashboard + Collaboration Control Room</h1>
            <p className="mt-2 max-w-2xl text-slate-300">
              Create dashboards, leave comments, and share assets from one interface connected to the live FastAPI backend.
            </p>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <span className="text-slate-300">Workspace ID</span>
            <input
              value={workspaceId}
              onChange={(event) => setWorkspaceId(event.target.value)}
              className="w-24 rounded-lg border border-white/20 bg-slate-950/80 px-3 py-2 text-white"
              inputMode="numeric"
            />
          </label>
        </header>

        <div className="grid gap-6 lg:grid-cols-3">
          <article className="rounded-3xl border border-cyan-300/20 bg-slate-950/60 p-5">
            <h2 className="text-lg font-medium text-cyan-100">Create Dashboard</h2>
            <form className="mt-4 space-y-3" onSubmit={createDashboard}>
              <input
                value={dashboardName}
                onChange={(event) => setDashboardName(event.target.value)}
                className="w-full rounded-lg border border-white/15 bg-slate-900 px-3 py-2"
                placeholder="Dashboard name"
              />
              <textarea
                value={dashboardDescription}
                onChange={(event) => setDashboardDescription(event.target.value)}
                className="h-24 w-full rounded-lg border border-white/15 bg-slate-900 px-3 py-2"
                placeholder="Dashboard description"
              />
              <button type="submit" disabled={isSubmitting} className="rounded-lg bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-70">
                Create
              </button>
            </form>
          </article>

          <article className="rounded-3xl border border-emerald-300/20 bg-slate-950/60 p-5">
            <h2 className="text-lg font-medium text-emerald-100">Post Comment</h2>
            <form className="mt-4 space-y-3" onSubmit={postComment}>
              <input
                value={commentEmail}
                onChange={(event) => setCommentEmail(event.target.value)}
                className="w-full rounded-lg border border-white/15 bg-slate-900 px-3 py-2"
                placeholder="user email"
              />
              <textarea
                value={commentMessage}
                onChange={(event) => setCommentMessage(event.target.value)}
                className="h-24 w-full rounded-lg border border-white/15 bg-slate-900 px-3 py-2"
                placeholder="Comment message"
              />
              <button type="submit" disabled={isSubmitting} className="rounded-lg bg-emerald-400 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-70">
                Comment
              </button>
            </form>
          </article>

          <article className="rounded-3xl border border-amber-300/20 bg-slate-950/60 p-5">
            <h2 className="text-lg font-medium text-amber-100">Share Dashboard</h2>
            <form className="mt-4 space-y-3" onSubmit={createShare}>
              <input
                value={shareEmail}
                onChange={(event) => setShareEmail(event.target.value)}
                className="w-full rounded-lg border border-white/15 bg-slate-900 px-3 py-2"
                placeholder="target email"
              />
              <select
                value={sharePermission}
                onChange={(event) => setSharePermission(event.target.value)}
                className="w-full rounded-lg border border-white/15 bg-slate-900 px-3 py-2"
              >
                <option value="view">view</option>
                <option value="edit">edit</option>
              </select>
              <button type="submit" disabled={isSubmitting} className="rounded-lg bg-amber-300 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-70">
                Share
              </button>
            </form>
          </article>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          <section className="rounded-3xl border border-white/10 bg-black/25 p-5">
            <h3 className="text-sm uppercase tracking-[0.2em] text-slate-300">Recent Dashboards</h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-200">
              {dashboards.length === 0 ? <li className="text-slate-400">No dashboards yet.</li> : null}
              {dashboards.map((item) => (
                <li key={item.id} className="rounded-lg border border-white/10 bg-slate-900/80 p-3">
                  <p className="font-medium">{item.name}</p>
                  <p className="text-slate-400">{item.description ?? 'No description'}</p>
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-3xl border border-white/10 bg-black/25 p-5">
            <h3 className="text-sm uppercase tracking-[0.2em] text-slate-300">Recent Comments</h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-200">
              {comments.length === 0 ? <li className="text-slate-400">No comments yet.</li> : null}
              {comments.map((item) => (
                <li key={item.id} className="rounded-lg border border-white/10 bg-slate-900/80 p-3">
                  <p className="font-medium">{item.user_email}</p>
                  <p className="text-slate-400">{item.message}</p>
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-3xl border border-white/10 bg-black/25 p-5">
            <h3 className="text-sm uppercase tracking-[0.2em] text-slate-300">Recent Shares</h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-200">
              {shares.length === 0 ? <li className="text-slate-400">No shares yet.</li> : null}
              {shares.map((item) => (
                <li key={item.id} className="rounded-lg border border-white/10 bg-slate-900/80 p-3">
                  <p className="font-medium">{item.target_email}</p>
                  <p className="text-slate-400">Permission: {item.permission}</p>
                </li>
              ))}
            </ul>
          </section>
        </div>

        <footer className="mt-6 rounded-2xl border border-white/10 bg-black/25 p-4 text-sm text-slate-300">
          <p>Status: {status}</p>
          {error ? <p className="mt-1 text-rose-300">Error: {error}</p> : null}
          <p className="mt-1 text-slate-400">API Base: {apiBase}</p>
        </footer>
      </section>
    </main>
  );
}

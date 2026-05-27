import {
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
} from '@tanstack/react-router';
import { HomePage } from '../features/workspaces/pages/HomePage';
import { WorkspacePage } from '../features/workspaces/pages/WorkspacePage';
import { WorkspaceLayout } from '../layouts/WorkspaceLayout';

const rootRoute = createRootRoute({
  component: () => <Outlet />,
});

const workspaceLayoutRoute = createRoute({
  getParentRoute: () => rootRoute,
  id: 'workspace-layout',
  component: WorkspaceLayout,
});

const homeRoute = createRoute({
  getParentRoute: () => workspaceLayoutRoute,
  path: '/',
  component: HomePage,
});

const workspaceRoute = createRoute({
  getParentRoute: () => workspaceLayoutRoute,
  path: '/workspace',
  component: WorkspacePage,
});

const routeTree = rootRoute.addChildren([
  workspaceLayoutRoute.addChildren([homeRoute, workspaceRoute]),
]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

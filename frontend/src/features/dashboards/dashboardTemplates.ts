export type DashboardTemplate = {
  id: string;
  label: string;
  name: string;
  description: string;
  note: string;
};

export const dashboardTemplates: DashboardTemplate[] = [
  {
    id: 'executive-summary',
    label: 'Executive summary',
    name: 'Executive Overview',
    description: 'Weekly KPI summary for leadership with the highest-level trends and exceptions.',
    note: 'Good for quick stakeholder review.',
  },
  {
    id: 'operations-review',
    label: 'Operations review',
    name: 'Operations Control Panel',
    description: 'Daily health view for operational metrics, alerts, and exceptions that need action.',
    note: 'Best for teams handling live operations.',
  },
  {
    id: 'analysis-deep-dive',
    label: 'Analysis deep dive',
    name: 'Trend Deep Dive',
    description: 'Exploratory dashboard for comparison, segmentation, and root-cause analysis.',
    note: 'Useful when a query needs follow-up investigation.',
  },
];

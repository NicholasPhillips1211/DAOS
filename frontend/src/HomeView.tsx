import { cardClass, Tooltip } from './components/ui';

type HomeViewProps = {
  onStartTour: () => void;
  onEnterWorkspace: () => void;
};

type FeatureCard = {
  id: string;
  badge: string;
  title: string;
  description: string;
  tooltip: string;
};

const features: FeatureCard[] = [
  {
    id: 'ingestion-section',
    badge: 'ING',
    title: 'Data ingestion',
    description: 'Upload CSV files, connect live databases, or sync APIs into an auditable workspace.',
    tooltip: 'View ingestion options',
  },
  {
    id: 'analysis-section',
    badge: 'SQL',
    title: 'Explore and analyze',
    description: 'Write SQL, inspect profiles, and turn query results into dashboard-ready assets.',
    tooltip: 'Try the SQL workflow',
  },
  {
    id: 'automation-section',
    badge: 'AI',
    title: 'AI automation',
    description: 'Generate operational plans with triggers, actions, and next steps from workspace signals.',
    tooltip: 'Generate an automation plan',
  },
  {
    id: 'collaboration-section',
    badge: 'COM',
    title: 'Collaborate',
    description: 'Comment, share dashboards, and keep team decisions connected to workspace assets.',
    tooltip: 'Review collaboration tools',
  },
  {
    id: 'governance-section',
    badge: 'GOV',
    title: 'Governance',
    description: 'Track access, audit events, lineage signals, and compliance-sensitive workflow activity.',
    tooltip: 'Configure governance policies',
  },
  {
    id: 'recommendations-section',
    badge: 'REC',
    title: 'Smart recommendations',
    description: 'Surface missing metrics, quality issues, and optimization opportunities from workspace context.',
    tooltip: 'View recommendations',
  },
];

const quickStartSteps = [
  {
    title: 'Upload your data',
    description: 'Use ingestion to upload a CSV and generate profile metadata.',
  },
  {
    title: 'Explore your data',
    description: 'Run SQL, preview results, and prepare the output for dashboards.',
  },
  {
    title: 'Operationalize insights',
    description: 'Create dashboards, share them with the team, and plan recurring automation.',
  },
];

export function HomeView({ onStartTour, onEnterWorkspace }: HomeViewProps) {
  return (
    <main className="relative min-h-screen overflow-hidden text-slate-100">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-[-8rem] top-[-8rem] h-72 w-72 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="absolute right-[-5rem] top-20 h-80 w-80 rounded-full bg-amber-300/15 blur-3xl" />
        <div className="absolute bottom-[-6rem] left-1/3 h-96 w-96 rounded-full bg-emerald-400/10 blur-3xl" />
      </div>

      <section className="relative mx-auto w-full max-w-7xl px-6 py-8 lg:px-10 lg:py-16">
        <HeroPanel onEnterWorkspace={onEnterWorkspace} onStartTour={onStartTour} />

        <div className="mb-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <FeatureCard key={feature.id} feature={feature} />
          ))}
        </div>

        <QuickStartPanel onStartTour={onStartTour} />

        <footer className="mt-12 text-center text-sm text-slate-400">
          <p>
            Built on FastAPI, React, and PostgreSQL. Local LLM ready.{' '}
            <Tooltip content="See the documentation">
              <a href="#" className="text-cyan-300 hover:text-cyan-200">
                Learn more
              </a>
            </Tooltip>
          </p>
        </footer>
      </section>
    </main>
  );
}

function HeroPanel({
  onEnterWorkspace,
  onStartTour,
}: {
  onEnterWorkspace: () => void;
  onStartTour: () => void;
}) {
  return (
    <div className="mb-12 rounded-[2.5rem] border border-white/10 bg-gradient-to-br from-slate-950/80 to-slate-950/50 p-8 shadow-[0_30px_120px_rgba(0,0,0,0.35)] backdrop-blur-xl md:p-12 lg:p-16">
      <div className="max-w-3xl">
        <p className="text-xs uppercase tracking-[0.5em] text-cyan-200/90">Welcome to DAOS</p>
        <h1 className="mt-4 text-5xl font-bold tracking-tight text-white md:text-6xl">
          Move From Data To Decisions
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
          DAOS is an operational analytics workspace for teams that need ingestion, SQL analysis, metadata,
          automation, and dashboards in one flow.
        </p>

        <div className="mt-10 flex flex-wrap gap-4">
          <Tooltip content="Start a step-by-step walkthrough of DAOS features">
            <button
              onClick={onStartTour}
              className="rounded-full bg-cyan-500 px-8 py-4 font-semibold text-slate-950 shadow-lg transition hover:bg-cyan-400 hover:shadow-xl"
            >
              Take the tour
            </button>
          </Tooltip>

          <Tooltip content="Jump directly into your workspace">
            <button
              onClick={onEnterWorkspace}
              className="rounded-full border-2 border-cyan-400/60 bg-white/5 px-8 py-4 font-semibold text-white transition hover:bg-white/10"
            >
              Enter workspace
            </button>
          </Tooltip>
        </div>
      </div>
    </div>
  );
}

function FeatureCard({ feature }: { feature: FeatureCard }) {
  return (
    <div id={feature.id} className={`${cardClass} p-6 transition hover:border-white/20`}>
      <div className="mb-3 inline-flex h-10 min-w-10 items-center justify-center rounded-full border border-cyan-300/20 bg-cyan-400/10 px-3 text-xs font-semibold tracking-[0.18em] text-cyan-100">
        {feature.badge}
      </div>
      <h3 className="mb-2 text-xl font-semibold text-white">{feature.title}</h3>
      <p className="text-sm leading-6 text-slate-300">{feature.description}</p>
      <Tooltip content={feature.tooltip} position="bottom">
        <button className="mt-4 text-xs font-medium text-cyan-300 hover:text-cyan-200">Learn more</button>
      </Tooltip>
    </div>
  );
}

function QuickStartPanel({ onStartTour }: { onStartTour: () => void }) {
  return (
    <div className={`${cardClass} p-8 md:p-10`}>
      <h2 className="mb-6 text-2xl font-bold text-white md:text-3xl">Get Started In 3 Steps</h2>

      <div className="grid gap-6 md:grid-cols-3">
        {quickStartSteps.map((step, index) => (
          <div key={step.title} className="space-y-3">
            <div className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-cyan-500 text-lg font-bold text-slate-950">
              {index + 1}
            </div>
            <h3 className="font-semibold text-white">{step.title}</h3>
            <p className="text-sm text-slate-300">{step.description}</p>
          </div>
        ))}
      </div>

      <div className="mt-10 flex flex-col items-center justify-between gap-4 border-t border-white/10 pt-8 sm:flex-row">
        <p className="text-sm text-slate-400">The guided tour walks through the core workspace flow.</p>
        <Tooltip content="See the full walkthrough">
          <button
            onClick={onStartTour}
            className="rounded-full border border-white/20 bg-white/10 px-6 py-2 text-sm font-medium text-white transition hover:bg-white/20"
          >
            Start the tour
          </button>
        </Tooltip>
      </div>
    </div>
  );
}

import type { AutomationPlanPayload } from '../../../../types/domain';

type AutomationRecipePanelProps = {
  parsedAutomation: AutomationPlanPayload | null;
};

export function AutomationRecipePanel({ parsedAutomation }: AutomationRecipePanelProps) {
  if (!parsedAutomation) {
    return null;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <AutomationList title="Triggers" items={parsedAutomation.triggers} />
      <AutomationList title="Actions" items={parsedAutomation.actions} />
    </div>
  );
}

function AutomationList({
  items,
  title,
}: {
  items: Array<{ name: string; description: string }>;
  title: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <p className="text-xs uppercase tracking-[0.25em] text-slate-400">{title}</p>
      <ul className="mt-3 space-y-2 text-sm text-slate-200">
        {items.map((item) => (
          <li key={item.name} className="rounded-xl border border-white/10 bg-slate-950/60 p-3">
            <p className="font-medium text-white">{item.name}</p>
            <p className="mt-1 text-slate-400">{item.description}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

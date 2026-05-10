import { useState } from 'react';

type TooltipProps = {
  content: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
};

export function Tooltip({ content, children, position = 'top' }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  const positionClasses: Record<string, string> = {
    top: 'bottom-full mb-2 left-1/2 -translate-x-1/2',
    bottom: 'top-full mt-2 left-1/2 -translate-x-1/2',
    left: 'right-full mr-2 top-1/2 -translate-y-1/2',
    right: 'left-full ml-2 top-1/2 -translate-y-1/2',
  };

  return (
    <div className="relative inline-block group">
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
      >
        {children}
      </div>

      {isVisible && (
        <div
          className={`absolute z-50 px-3 py-2 text-xs text-white bg-slate-900 rounded-lg border border-cyan-400/50 shadow-lg pointer-events-none whitespace-nowrap ${positionClasses[position]}`}
        >
          {content}
          <div className="absolute w-2 h-2 bg-slate-900 border border-cyan-400/50 transform -z-10" 
            style={{
              [position === 'top' ? 'bottom' : position === 'bottom' ? 'top' : position === 'left' ? 'right' : 'left']: '-4px',
              [position === 'top' || position === 'bottom' ? 'left' : 'top']: '50%',
              transform: position === 'top' || position === 'bottom' 
                ? 'translateX(-50%) rotate(45deg)' 
                : 'translateY(-50%) rotate(45deg)',
            }}
          />
        </div>
      )}
    </div>
  );
}

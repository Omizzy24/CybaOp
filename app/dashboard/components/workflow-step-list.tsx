"use client";

import type { WorkflowStep } from "@/app/dashboard/types";

interface WorkflowStepListProps {
  steps: WorkflowStep[];
  currentStep: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  completed: "bg-lime",
  active: "bg-amber",
  failed: "bg-rose",
  skipped: "bg-sky",
  pending: "bg-muted",
};

const STATUS_LABELS: Record<string, string> = {
  completed: "Done",
  active: "Running",
  failed: "Failed",
  skipped: "Skipped",
  pending: "Pending",
};

export function WorkflowStepList({ steps, currentStep }: WorkflowStepListProps) {
  return (
    <div className="space-y-0">
      {steps.map((step, i) => {
        const isActive = step.step_name === currentStep;
        const isLast = i === steps.length - 1;
        const dotColor = STATUS_COLORS[step.status] ?? "bg-muted";
        const label = STATUS_LABELS[step.status] ?? step.status;

        return (
          <div key={`${step.step_name}-${i}`} className="flex gap-3">
            {/* Dot + connecting line */}
            <div className="flex flex-col items-center">
              <span
                className={`w-3 h-3 rounded-full flex-shrink-0 ${dotColor} ${isActive ? "animate-pulse" : ""}`}
              />
              {!isLast && (
                <span className="w-px flex-1 min-h-6 border-l border-border" />
              )}
            </div>

            {/* Step content */}
            <div className={`pb-4 ${isLast ? "pb-0" : ""}`}>
              <p className="text-sm font-mono leading-tight">{step.label}</p>
              <p className="text-xs text-muted font-mono mt-0.5">{label}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

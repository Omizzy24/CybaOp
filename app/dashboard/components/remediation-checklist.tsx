"use client";

interface RemediationStep {
  action: string;
  expected_impact: string;
  status: string;
}

interface RemediationChecklistProps {
  steps: RemediationStep[];
  currentIndex: number;
}

export function RemediationChecklist({ steps, currentIndex }: RemediationChecklistProps) {
  return (
    <div className="space-y-2">
      {steps.map((step, i) => {
        const isCurrent = i === currentIndex;
        const isCompleted = step.status === "completed";
        const isSkipped = step.status === "skipped";

        return (
          <div
            key={i}
            className={`rounded-xl border bg-surface p-3 sm:p-4 space-y-1 ${
              isCurrent
                ? "border-amber/40 bg-amber-dim"
                : "border-border"
            }`}
          >
            <div className="flex items-start gap-3">
              {/* Checkbox */}
              <span
                className={`mt-0.5 flex-shrink-0 w-4 h-4 rounded border flex items-center justify-center text-[10px] ${
                  isCompleted
                    ? "bg-lime border-lime text-background"
                    : isSkipped
                      ? "bg-sky border-sky text-background"
                      : "border-border"
                }`}
              >
                {isCompleted && "✓"}
                {isSkipped && "–"}
              </span>

              <div className="min-w-0 flex-1">
                <p
                  className={`text-sm font-mono ${
                    isCompleted
                      ? "line-through text-muted"
                      : isSkipped
                        ? "text-muted"
                        : "text-foreground"
                  }`}
                >
                  {step.action}
                </p>
                <p className="text-xs text-muted font-mono mt-0.5">
                  {step.expected_impact}
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

import type { HTMLAttributes, ReactNode } from "react";
import { AlertTriangle, CheckCircle2, Info } from "lucide-react";

import { cn } from "@/components/ui/utils";

type AlertTone = "info" | "success" | "warning" | "danger";

const toneClasses: Record<AlertTone, string> = {
  info: "border-info/30 bg-info/10 text-info",
  success: "border-success/30 bg-success/10 text-brand-deep",
  warning: "border-warning/35 bg-warning/10 text-[#7a4318]",
  danger: "border-danger/35 bg-danger/10 text-danger"
};

export function Alert({
  tone = "info",
  title,
  children,
  className,
  ...props
}: HTMLAttributes<HTMLDivElement> & { tone?: AlertTone; title?: string; children: ReactNode }) {
  const Icon = tone === "success" ? CheckCircle2 : tone === "info" ? Info : AlertTriangle;
  return (
    <div
      className={cn("flex gap-3 rounded-md border p-4", toneClasses[tone], className)}
      role={tone === "danger" || tone === "warning" ? "alert" : "status"}
      {...props}
    >
      <Icon aria-hidden="true" className="mt-1 h-5 w-5 shrink-0" />
      <div>
        {title ? <p className="font-bold">{title}</p> : null}
        <div className="text-sm leading-6">{children}</div>
      </div>
    </div>
  );
}

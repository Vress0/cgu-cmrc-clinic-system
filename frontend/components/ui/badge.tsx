import type { HTMLAttributes } from "react";

import { cn } from "@/components/ui/utils";

type BadgeTone = "default" | "success" | "warning" | "danger" | "info" | "cinnabar";

const toneClasses: Record<BadgeTone, string> = {
  default: "border-line bg-paper text-ink",
  success: "border-success/30 bg-success/10 text-brand-deep",
  warning: "border-warning/30 bg-warning/10 text-[#7a4318]",
  danger: "border-danger/35 bg-danger/10 text-danger",
  info: "border-info/30 bg-info/10 text-info",
  cinnabar: "border-cinnabar bg-cinnabar text-white"
};

export function Badge({
  tone = "default",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: BadgeTone }) {
  return (
    <span
      className={cn(
        "inline-flex min-h-7 items-center rounded-md border px-2.5 py-1 text-sm font-bold",
        toneClasses[tone],
        className
      )}
      {...props}
    />
  );
}

export function StatusTag({ status }: Readonly<{ status: string }>) {
  const labels: Record<string, string> = {
    REGISTERED: "已掛號",
    WAITING_FOR_CLINIC: "候診中",
    IN_CONSULTATION: "看診中",
    WAITING_FOR_PHARMACY: "待藥局",
    DISPENSING: "調劑中",
    WAITING_FOR_VERIFICATION: "待核對",
    VERIFIED: "已核對",
    WAITING_FOR_PICKUP: "待發藥",
    DISPENSED: "已發藥",
    COMPLETED: "已完成",
    CANCELLED: "已取消",
    ACTIVE: "進行中",
    DRAFT: "草稿",
    ENDED: "已結束",
    ARCHIVED: "已封存"
  };
  const tone =
    status === "COMPLETED" || status === "ACTIVE" || status === "DISPENSED" || status === "VERIFIED"
      ? "success"
      : status === "CANCELLED"
        ? "danger"
        : status.includes("WAITING")
          ? "warning"
          : status === "IN_CONSULTATION" || status === "DISPENSING"
            ? "info"
            : "default";
  return <Badge tone={tone}>{labels[status] ?? status}</Badge>;
}

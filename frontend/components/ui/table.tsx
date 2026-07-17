import type { HTMLAttributes } from "react";

import { cn } from "@/components/ui/utils";

export function DataTable({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("overflow-hidden rounded-md border border-line bg-panel", className)} {...props} />;
}

export function TableRow({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("border-b border-line last:border-b-0", className)} {...props} />;
}

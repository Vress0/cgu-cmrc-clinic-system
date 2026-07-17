import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/components/ui/utils";

export function Tabs({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-wrap gap-2", className)} {...props} />;
}

export function TabButton({
  active,
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { active?: boolean }) {
  return (
    <button
      className={cn(
        "min-h-11 rounded-md border px-4 py-2 font-bold transition",
        active ? "border-brand bg-brand text-white" : "border-line bg-panel text-ink hover:bg-bamboo/40",
        className
      )}
      {...props}
    />
  );
}

import type { InputHTMLAttributes, LabelHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

import { cn } from "@/components/ui/utils";

export function FormField({
  label,
  hint,
  error,
  children
}: Readonly<{ label: string; hint?: string; error?: string; children: ReactNode }>) {
  return (
    <label className="block">
      <span className="mb-2 block font-bold text-ink">{label}</span>
      {children}
      {hint ? <span className="mt-1 block text-sm leading-6 text-muted">{hint}</span> : null}
      {error ? <span className="mt-1 block text-sm font-bold text-danger">{error}</span> : null}
    </label>
  );
}

const fieldClass =
  "min-h-12 w-full rounded-md border border-line bg-white/80 px-4 py-3 text-ink shadow-insetline transition placeholder:text-muted/70 focus:border-brand";

export function TextInput({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(fieldClass, className)} {...props} />;
}

export function SelectInput({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={cn(fieldClass, className)} {...props} />;
}

export function TextareaInput({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn(fieldClass, "min-h-28", className)} {...props} />;
}

export function FieldLabel({ className, ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return <label className={cn("mb-2 block font-bold text-ink", className)} {...props} />;
}

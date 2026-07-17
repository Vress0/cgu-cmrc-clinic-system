import { Alert } from "@/components/ui/alert";

export function Toast({ message, tone = "success" }: Readonly<{ message: string | null; tone?: "success" | "danger" | "info" }>) {
  if (!message) return null;
  return (
    <div className="fixed bottom-5 right-5 z-40 w-[min(92vw,360px)]" aria-live="polite" aria-atomic="true">
      <Alert tone={tone}>{message}</Alert>
    </div>
  );
}

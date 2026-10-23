export function severityInfo(severity: number): {
  label: string;
  badge: string;
  dot: string;
  bar: string;
  text: string;
} {
  if (severity >= 4) {
    return {
      label: "Crítico",
      badge: "border-brand-500/25 bg-brand-500/10 text-brand-400",
      dot: "bg-brand-500",
      bar: "bg-brand-500",
      text: "text-brand-400",
    };
  }
  if (severity === 3) {
    return {
      label: "Importante",
      badge: "border-amber-400/25 bg-amber-400/10 text-amber-400",
      dot: "bg-amber-400",
      bar: "bg-amber-400",
      text: "text-amber-400",
    };
  }
  return {
    label: "A mejorar",
    badge: "border-sky-400/25 bg-sky-400/10 text-sky-400",
    dot: "bg-sky-400",
    bar: "bg-sky-400",
    text: "text-sky-400",
  };
}

export default function Loading() {
  return (
    <div className="animate-pulse">
      <div className="h-3 w-16 rounded bg-white/5" />
      <div className="mt-4 h-8 w-64 rounded-lg bg-white/5" />
      <div className="mt-3 h-3 w-96 max-w-full rounded bg-white/5" />
      <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="panel h-28 p-5">
            <div className="h-3 w-14 rounded bg-white/5" />
            <div className="mt-4 h-7 w-20 rounded bg-white/5" />
            <div className="mt-3 h-2.5 w-28 rounded bg-white/5" />
          </div>
        ))}
      </div>
      <div className="mt-4 grid gap-4 xl:grid-cols-[1.7fr_1fr]">
        <div className="panel h-64" />
        <div className="panel h-64" />
      </div>
    </div>
  );
}

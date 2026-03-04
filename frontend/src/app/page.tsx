import { redirect } from "next/navigation";
import Link from "next/link";
import { getProducts } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Home() {
  let products;
  try {
    products = await getProducts();
  } catch {
    return (
      <main className="flex min-h-screen items-center justify-center p-8">
        <div className="text-center space-y-3">
          <p className="font-display font-bold text-xl tracking-tight">PULSE</p>
          <p className="font-mono text-xs text-muted-foreground">
            Could not connect to the API. Make sure the backend is running at{" "}
            <code className="text-primary">
              {process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000"}
            </code>
          </p>
        </div>
      </main>
    );
  }

  const active = products.filter((p) => p.is_active);

  if (active.length === 1) {
    redirect(`/products/${active[0].slug}/dashboard`);
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-8">
      <div className="w-full max-w-lg space-y-8">
        {/* Wordmark */}
        <div className="text-center space-y-1">
          <h1 className="font-display font-bold text-2xl tracking-[0.25em] uppercase text-foreground">
            PULSE
          </h1>
          <p className="font-mono text-[10px] tracking-[0.2em] uppercase text-muted-foreground">
            Select a product
          </p>
        </div>

        {/* Product list */}
        <div className="border border-border rounded-sm overflow-hidden">
          {active.map((p, i) => (
            <Link
              key={p.id}
              href={`/products/${p.slug}/dashboard`}
              className={`flex items-center gap-4 px-5 py-4 transition-colors hover:bg-card focus-visible:outline-none focus-visible:bg-card${i > 0 ? " border-t border-border" : ""}`}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
              <div className="flex-1 min-w-0 space-y-0.5">
                <p className="font-display font-semibold text-sm tracking-tight text-foreground">
                  {p.name}
                </p>
                {p.description && (
                  <p className="font-mono text-[10px] text-muted-foreground truncate">
                    {p.description}
                  </p>
                )}
              </div>
              <span className="font-mono text-[10px] tracking-widest text-muted-foreground shrink-0">
                →
              </span>
            </Link>
          ))}
          {active.length === 0 && (
            <p className="px-5 py-4 font-mono text-[10px] tracking-widest uppercase text-muted-foreground/50">
              No active products.
            </p>
          )}
        </div>
      </div>
    </main>
  );
}

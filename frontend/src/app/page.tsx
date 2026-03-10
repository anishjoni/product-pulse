import { redirect } from "next/navigation";
import Link from "next/link";
import { getProducts } from "@/lib/api";
import { AddProductButton } from "@/components/AddProductButton";

export const dynamic = "force-dynamic";

export default async function Home() {
  let products;
  try {
    products = await getProducts();
  } catch {
    return (
      <main className="flex min-h-screen items-center justify-center p-8">
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center gap-2 mb-4">
            <span className="h-2.5 w-2.5 rounded-full bg-primary" />
            <span className="text-base font-semibold tracking-tight">Pulse</span>
          </div>
          <p className="text-sm text-muted-foreground">
            Could not connect to the API. Make sure the backend is running at{" "}
            <code className="text-xs bg-muted px-1.5 py-0.5 rounded text-foreground">
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
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="w-full max-w-lg space-y-6">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-primary" />
              <span className="text-base font-semibold tracking-tight">Pulse</span>
            </div>
            <p className="text-sm text-muted-foreground pl-5">
              {active.length === 0
                ? "No products yet. Add one to get started."
                : "Select a product to view its dashboard."}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/compare" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
              Compare topics →
            </Link>
            <AddProductButton />
          </div>
        </div>

        {active.length > 0 && (
          <div className="space-y-2">
            {active.map((p) => (
              <Link key={p.id} href={`/products/${p.slug}/dashboard`}>
                <div className="rounded bg-card border border-border overflow-hidden transition-colors hover:border-primary/40 flex group">
                  <div className="w-[3px] shrink-0 bg-primary opacity-60 group-hover:opacity-100 transition-opacity" />
                  <div className="px-4 py-3">
                    <p className="text-sm font-medium">{p.name}</p>
                    {p.description && (
                      <p className="text-xs text-muted-foreground mt-0.5">{p.description}</p>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

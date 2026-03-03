import { redirect } from "next/navigation";
import Link from "next/link";
import { getProducts } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const dynamic = "force-dynamic";

export default async function Home() {
  let products;
  try {
    products = await getProducts();
  } catch {
    return (
      <main className="flex min-h-screen items-center justify-center p-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2">Product Pulse</h1>
          <p className="text-muted-foreground">
            Could not connect to the API. Make sure the backend is running at{" "}
            <code className="text-sm bg-muted px-1 rounded">
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
    <main className="min-h-screen p-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Product Pulse</h1>
        <p className="text-muted-foreground mb-8">Select a product to view its dashboard.</p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {active.map((p) => (
            <Link key={p.id} href={`/products/${p.slug}/dashboard`}>
              <Card className="cursor-pointer hover:shadow-md transition-shadow">
                <CardHeader>
                  <CardTitle>{p.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{p.description ?? "No description."}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}

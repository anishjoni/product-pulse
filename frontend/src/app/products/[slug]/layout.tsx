import Link from "next/link";
import { getProducts } from "@/lib/api";
import { Separator } from "@/components/ui/separator";

export const dynamic = "force-dynamic";

interface Props {
  children: React.ReactNode;
  params: { slug: string };
}

export default async function ProductLayout({ children, params }: Props) {
  const products = await getProducts();
  const product = products.find((p) => p.slug === params.slug);

  const navLinks = [
    { href: `/products/${params.slug}/dashboard`, label: "Dashboard" },
    { href: `/products/${params.slug}/feed`, label: "Feed" },
    { href: `/products/${params.slug}/trends`, label: "Trends" },
    { href: `/products/${params.slug}/settings`, label: "Settings" },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b px-6 py-3 flex items-center gap-6">
        <Link href="/" className="font-bold text-lg tracking-tight">
          Pulse
        </Link>
        {product && (
          <>
            <Separator orientation="vertical" className="h-5" />
            <span className="text-muted-foreground text-sm font-medium">{product.name}</span>
          </>
        )}
        <nav className="ml-auto flex gap-4 text-sm">
          {navLinks.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              {l.label}
            </Link>
          ))}
        </nav>
      </header>
      <div className="flex-1">{children}</div>
    </div>
  );
}

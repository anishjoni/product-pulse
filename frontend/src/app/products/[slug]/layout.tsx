import Link from "next/link";
import { getProducts } from "@/lib/api";

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
    <div className="min-h-screen flex flex-col bg-background">
      <header className="border-b border-border flex items-stretch h-11 shrink-0">
        {/* Logo mark */}
        <Link
          href="/"
          className="flex items-center gap-2 px-5 border-r border-border hover:bg-card transition-colors"
        >
          <span className="font-display font-bold text-xs tracking-[0.25em] uppercase text-foreground">
            PULSE
          </span>
          <span className="h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
        </Link>

        {/* Product name */}
        {product && (
          <div className="flex items-center px-4 border-r border-border">
            <span className="font-mono text-[11px] text-muted-foreground tracking-wide">
              {product.name.toUpperCase()}
            </span>
          </div>
        )}

        {/* Nav links — right-aligned, each in its own bordered cell */}
        <nav className="ml-auto flex items-stretch">
          {navLinks.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="flex items-center px-5 border-l border-border font-display font-semibold text-[11px] tracking-[0.15em] uppercase text-muted-foreground hover:text-foreground hover:bg-card transition-colors"
            >
              {l.label}
            </Link>
          ))}
        </nav>
      </header>

      <div className="flex-1 min-w-0">{children}</div>
    </div>
  );
}

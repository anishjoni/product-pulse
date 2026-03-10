import Link from "next/link";
import { getProducts } from "@/lib/api";
import { NavLinks } from "@/components/NavLinks";
import { ThemeToggle } from "@/components/ThemeToggle";
import { SearchPalette } from "@/components/SearchPalette";
import { SearchTrigger } from "@/components/SearchTrigger";
import { ProductSwitcher } from "@/components/ProductSwitcher";

export const dynamic = "force-dynamic";

interface Props {
  children: React.ReactNode;
  params: { slug: string };
}

export default async function ProductLayout({ children, params }: Props) {
  const products = await getProducts();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-border h-12 px-5 flex items-center gap-3 shrink-0">
        <Link href="/" className="flex items-center gap-1.5 shrink-0">
          <span className="h-2 w-2 rounded-full bg-primary" />
          <span className="text-sm font-semibold tracking-tight">Pulse</span>
        </Link>
        <span className="text-border select-none">/</span>
        <ProductSwitcher products={products} currentSlug={params.slug} />
        <div className="ml-auto flex items-center gap-1">
          <NavLinks slug={params.slug} />
          <div className="w-px h-4 bg-border mx-1" />
          <SearchTrigger />
          <ThemeToggle />
        </div>
      </header>
      <div className="flex-1">{children}</div>
      <SearchPalette />
    </div>
  );
}

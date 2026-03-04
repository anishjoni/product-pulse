import Link from "next/link";
import { getProducts } from "@/lib/api";
import { NavLinks } from "@/components/NavLinks";

export const dynamic = "force-dynamic";

interface Props {
  children: React.ReactNode;
  params: { slug: string };
}

export default async function ProductLayout({ children, params }: Props) {
  const products = await getProducts();
  const product = products.find((p) => p.slug === params.slug);

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-border h-12 px-5 flex items-center gap-3 shrink-0">
        <Link href="/" className="flex items-center gap-1.5 shrink-0">
          <span className="h-2 w-2 rounded-full bg-primary" />
          <span className="text-sm font-semibold tracking-tight">Pulse</span>
        </Link>
        {product && (
          <>
            <span className="text-border select-none">/</span>
            <span className="text-sm text-muted-foreground truncate min-w-0">
              {product.name}
            </span>
          </>
        )}
        <div className="ml-auto">
          <NavLinks slug={params.slug} />
        </div>
      </header>
      <div className="flex-1">{children}</div>
    </div>
  );
}

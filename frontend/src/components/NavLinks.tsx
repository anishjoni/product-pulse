"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavLinksProps {
  slug: string;
}

export function NavLinks({ slug }: NavLinksProps) {
  const pathname = usePathname();

  const links = [
    { href: `/products/${slug}/dashboard`, label: "Dashboard" },
    { href: `/products/${slug}/feed`, label: "Feed" },
    { href: `/products/${slug}/trends`, label: "Trends" },
    { href: `/products/${slug}/settings`, label: "Settings" },
  ];

  return (
    <nav className="flex items-center gap-1">
      {links.map((l) => {
        const active = pathname === l.href;
        return (
          <Link
            key={l.href}
            href={l.href}
            className={`px-3 py-1.5 text-sm rounded transition-colors ${
              active
                ? "text-foreground bg-muted"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
            }`}
          >
            {l.label}
          </Link>
        );
      })}
    </nav>
  );
}

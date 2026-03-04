"use client";

import { useEffect, useState } from "react";

export function SearchTrigger() {
  const [isMac, setIsMac] = useState(false);

  useEffect(() => {
    setIsMac(navigator.platform.toUpperCase().includes("MAC"));
  }, []);

  function open() {
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true, bubbles: true }));
  }

  return (
    <button
      onClick={open}
      className="flex items-center gap-2 px-2 py-1 rounded text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors"
      aria-label="Search posts"
    >
      <svg
        width="13" height="13" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      >
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
      <kbd className="hidden sm:inline text-[10px] border border-border rounded px-1 py-0.5">
        {isMac ? "⌘K" : "^K"}
      </kbd>
    </button>
  );
}

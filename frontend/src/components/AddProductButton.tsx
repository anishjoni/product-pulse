"use client";

import { useState } from "react";
import { AddProductModal } from "@/components/AddProductModal";

export function AddProductButton() {
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md border border-border text-muted-foreground hover:text-foreground hover:border-primary/50 transition-colors"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        New product
      </button>

      {showModal && <AddProductModal onClose={() => setShowModal(false)} />}
    </>
  );
}

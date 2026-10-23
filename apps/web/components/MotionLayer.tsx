"use client";

import { useEffect } from "react";

/**
 * Capa ambiental reactiva al ratón. No renderiza contenido: solo dos orbes
 * con parallax, un halo que sigue al cursor y el resaltado de los paneles.
 * Se desactiva en táctil y con prefers-reduced-motion.
 */
export function MotionLayer() {
  useEffect(() => {
    const root = document.documentElement;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
    const finePointer = window.matchMedia("(pointer: fine)");
    if (reduce.matches || !finePointer.matches) return;

    let frame = 0;
    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let activePanel: HTMLElement | null = null;

    const paint = () => {
      frame = 0;
      root.style.setProperty("--pointer-x", `${mouseX}px`);
      root.style.setProperty("--pointer-y", `${mouseY}px`);
      root.style.setProperty(
        "--parallax-x",
        ((mouseX / window.innerWidth - 0.5) * 2).toFixed(3),
      );
      root.style.setProperty(
        "--parallax-y",
        ((mouseY / window.innerHeight - 0.5) * 2).toFixed(3),
      );

      const hovered = document.elementFromPoint(mouseX, mouseY);
      const panel =
        hovered instanceof Element
          ? (hovered.closest(".panel") as HTMLElement | null)
          : null;

      if (panel !== activePanel) {
        activePanel?.classList.remove("is-lit");
        activePanel?.style.setProperty("--rx", "0deg");
        activePanel?.style.setProperty("--ry", "0deg");
        activePanel = panel;
        activePanel?.classList.add("is-lit");
      }

      if (activePanel) {
        const rect = activePanel.getBoundingClientRect();
        activePanel.style.setProperty("--mx", `${mouseX - rect.left}px`);
        activePanel.style.setProperty("--my", `${mouseY - rect.top}px`);

        if (activePanel.hasAttribute("data-tilt")) {
          const x = (mouseX - (rect.left + rect.width / 2)) / rect.width;
          const y = (mouseY - (rect.top + rect.height / 2)) / rect.height;
          activePanel.style.setProperty("--rx", `${(-y * 5).toFixed(2)}deg`);
          activePanel.style.setProperty("--ry", `${(x * 5).toFixed(2)}deg`);
        }
      }
    };

    const onMove = (event: PointerEvent) => {
      mouseX = event.clientX;
      mouseY = event.clientY;
      root.classList.add("has-pointer");
      if (!frame) frame = window.requestAnimationFrame(paint);
    };

    const onLeave = () => {
      root.classList.remove("has-pointer");
      activePanel?.classList.remove("is-lit");
      activePanel?.style.setProperty("--rx", "0deg");
      activePanel?.style.setProperty("--ry", "0deg");
      activePanel = null;
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    document.addEventListener("pointerleave", onLeave);
    window.addEventListener("blur", onLeave);

    return () => {
      window.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerleave", onLeave);
      window.removeEventListener("blur", onLeave);
      if (frame) window.cancelAnimationFrame(frame);
      onLeave();
    };
  }, []);

  return (
    <div className="ambient" aria-hidden="true">
      <span className="ambient-orb ambient-orb-a" />
      <span className="ambient-orb ambient-orb-b" />
      <span className="ambient-grid" />
      <span className="cursor-glow" />
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";

interface CountUpProps {
  end: number;
  duration?: number;
  suffix?: string;
  decimals?: number;
}

function easeOut(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

export function CountUp({ end, duration = 1200, suffix = "", decimals = 0 }: CountUpProps) {
  const [display, setDisplay] = useState("0");
  const [hasAnimated, setHasAnimated] = useState(false);
  const [scale, setScale] = useState(1);
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (hasAnimated) return;

    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated) {
          setHasAnimated(true);
          animate();
          observer.disconnect();
        }
      },
      { threshold: 0.3 }
    );

    observer.observe(el);
    return () => observer.disconnect();

    function animate() {
      const start = performance.now();

      function tick(now: number) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = easeOut(progress);
        const current = eased * end;

        if (decimals > 0) {
          setDisplay(current.toFixed(decimals));
        } else {
          setDisplay(Math.round(current).toLocaleString());
        }

        if (progress < 1) {
          requestAnimationFrame(tick);
        } else {
          // Final value
          if (decimals > 0) {
            setDisplay(end.toFixed(decimals));
          } else {
            setDisplay(end.toLocaleString());
          }
          // Subtle scale pop
          setScale(1.02);
          setTimeout(() => setScale(1), 150);
        }
      }

      requestAnimationFrame(tick);
    }
  }, [end, duration, decimals, hasAnimated]);

  return (
    <span
      ref={ref}
      style={{
        transform: `scale(${scale})`,
        transition: "transform 150ms ease-out",
        display: "inline-block",
        fontVariantNumeric: "tabular-nums",
      }}
    >
      {display}{suffix}
    </span>
  );
}

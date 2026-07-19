"use client";

import { useEffect, useRef, useState } from "react";

const FRAME_COUNT = 48;

function frameSrc(i: number): string {
  return `/frames/frame_${String(Math.min(Math.max(i + 1, 1), FRAME_COUNT)).padStart(3, "0")}.png`;
}

export function ScrollFrames({ frame = 0 }: { frame?: number }) {
  const [ready, setReady] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imagesRef = useRef<HTMLImageElement[]>([]);
  const animatedRef = useRef(0);
  const rafRef = useRef(0);
  const targetRef = useRef(0);
  const velocityRef = useRef(0);

  useEffect(() => {
    let count = 0;
    const images: HTMLImageElement[] = [];
    for (let i = 0; i < FRAME_COUNT; i++) {
      const img = new Image();
      img.onload = img.onerror = () => {
        count++;
        if (count >= FRAME_COUNT) {
          imagesRef.current = images;
          setReady(true);
        }
      };
      img.src = frameSrc(i);
      images.push(img);
    }
  }, []);

  useEffect(() => {
    targetRef.current = frame;
  }, [frame]);

  useEffect(() => {
    if (!ready) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: false });
    if (!ctx) return;

    const images = imagesRef.current;

    const draw = () => {
      // Spring-damper physics for ultra-smooth motion
      const target = targetRef.current;
      const current = animatedRef.current;
      const diff = target - current;

      // Spring force + damping for natural deceleration
      const spring = 0.04;
      const damping = 0.82;
      velocityRef.current = velocityRef.current * damping + diff * spring;
      animatedRef.current += velocityRef.current;

      // Snap when very close
      if (Math.abs(diff) < 0.001 && Math.abs(velocityRef.current) < 0.001) {
        animatedRef.current = target;
        velocityRef.current = 0;
      }

      // Resize canvas to match CSS size
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }

      const exact = Math.max(0, Math.min(FRAME_COUNT - 1, animatedRef.current));
      const floor = Math.floor(exact);
      const ceil = Math.min(FRAME_COUNT - 1, floor + 1);
      const blend = exact - floor;

      const imgA = images[floor];
      if (imgA?.complete && imgA.naturalWidth > 0) {
        ctx.globalAlpha = 1;
        ctx.drawImage(imgA, 0, 0, w, h);

        // Blend next frame on top for sub-frame smoothness
        if (blend > 0.005 && ceil !== floor) {
          const imgB = images[ceil];
          if (imgB?.complete && imgB.naturalWidth > 0) {
            ctx.globalAlpha = blend;
            ctx.drawImage(imgB, 0, 0, w, h);
          }
        }
      }

      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(rafRef.current);
  }, [ready]);

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 w-full h-full transition-opacity duration-1000 ${ready ? "opacity-100" : "opacity-0"}`}
      style={{ willChange: "contents" }}
    />
  );
}

export { FRAME_COUNT };

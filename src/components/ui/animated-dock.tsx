"use client"

import * as React from "react"
import { useRef } from "react"
import {
  MotionValue,
  motion,
  useMotionValue,
  useSpring,
  useTransform,
} from "motion/react"
import clsx from "clsx"
import { twMerge } from "tailwind-merge"

const cn = (...args: any[]) => twMerge(clsx(args))

export interface DockItemData {
  id: string
  Icon: React.ReactNode
  label: string
  onClick?: () => void
  isActive?: boolean
}

export interface AnimatedDockProps {
  className?: string
  items: DockItemData[]
}

export const AnimatedDock = ({ className, items }: AnimatedDockProps) => {
  const mouseY = useMotionValue(Infinity)

  return (
    <motion.div
      onMouseMove={(e) => mouseY.set(e.pageY)}
      onMouseLeave={() => mouseY.set(Infinity)}
      className={cn(
        "flex flex-col items-center gap-3 py-3",
        className,
      )}
    >
      {items.map((item) => (
        <DockItem key={item.id} mouseY={mouseY} isActive={item.isActive}>
          <button
            onClick={item.onClick}
            className="flex items-center justify-center w-full h-full text-inherit"
            title={item.label}
          >
            {item.Icon}
          </button>
        </DockItem>
      ))}
    </motion.div>
  )
}

interface DockItemProps {
  mouseY: MotionValue<number>
  children: React.ReactNode
  isActive?: boolean
}

export const DockItem = ({ mouseY, children, isActive }: DockItemProps) => {
  const ref = useRef<HTMLDivElement>(null)

  const distance = useTransform(mouseY, (val) => {
    const bounds = ref.current?.getBoundingClientRect() ?? { y: 0, height: 0 }
    return val - bounds.y - bounds.height / 2
  })

  const sizeSync = useTransform(distance, [-100, 0, 100], [40, 56, 40])
  const size = useSpring(sizeSync, {
    mass: 0.1,
    stiffness: 150,
    damping: 12,
  })

  const iconScale = useTransform(size, [40, 56], [1, 1.3])
  const iconSpring = useSpring(iconScale, {
    mass: 0.1,
    stiffness: 150,
    damping: 12,
  })

  return (
    <motion.div
      ref={ref}
      style={{ width: size, height: size }}
      className={cn(
        "rounded-xl flex items-center justify-center transition-colors",
        isActive
          ? "bg-cyan-500/20 text-cyan-400"
          : "bg-zinc-800/50 text-zinc-400 hover:text-zinc-200",
      )}
    >
      {isActive && (
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-cyan-400 rounded-r-full" />
      )}
      <motion.div
        style={{ scale: iconSpring }}
        className="flex items-center justify-center w-full h-full"
      >
        {children}
      </motion.div>
    </motion.div>
  )
}

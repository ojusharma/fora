"use client"

import type React from "react"

import { useState, useRef } from "react"
import { TaskCard } from "./task-card"
import { X, Check, RotateCcw, Star } from "lucide-react"
import { Button } from "@/components/ui/button"

interface Task {
  id: string | number
  title: string
  description: string
  reward?: string
  location?: string
  timeAgo?: string
  category?: string
  postedBy?: string
  coverImage?: string
}

const sampleTasks: Task[] = [
  {
    id: 1,
    title: "Help hang string lights",
    description:
      "Need help putting up LED string lights in my dorm room. Should take about 30 minutes. I have all the materials!",
    reward: "$15",
    location: "West Campus Dorms",
    timeAgo: "2h ago",
    category: "Setup",
    postedBy: "Sarah M.",
    coverImage: "/cozy-dorm-room-with-warm-lighting.jpg",
  },
  {
    id: 2,
    title: "Move furniture",
    description:
      "Moving a desk and bookshelf from storage to my apartment. Need someone with a car. Heavy lifting involved.",
    reward: "$30",
    location: "North Apartments",
    timeAgo: "4h ago",
    category: "Moving",
    postedBy: "Alex K.",
    coverImage: "/furniture-and-moving-boxes-in-apartment.jpg",
  },
  {
    id: 3,
    title: "Set up TV and speakers",
    description:
      "Just got a new TV and sound system. Need help mounting the TV on the wall and setting up the speakers properly.",
    reward: "$25",
    location: "East Residence Hall",
    timeAgo: "6h ago",
    category: "Tech Setup",
    postedBy: "Jordan L.",
    coverImage: "/modern-tv-and-speaker-setup-in-living-room.jpg",
  },
  {
    id: 4,
    title: "Assemble IKEA furniture",
    description: "Have 2 bookshelves and a desk from IKEA that need assembling. All tools provided. Pizza included!",
    reward: "$20 + Pizza",
    location: "South Campus",
    timeAgo: "1d ago",
    category: "Assembly",
    postedBy: "Mike T.",
    coverImage: "/ikea-furniture-boxes-ready-for-assembly.jpg",
  },
  {
    id: 5,
    title: "Help with closet organization",
    description: "Need help organizing my closet and installing some shelving units. Should take about an hour.",
    reward: "$18",
    location: "West Campus",
    timeAgo: "1d ago",
    category: "Organization",
    postedBy: "Emma P.",
    coverImage: "/organized-closet-with-shelving-units.jpg",
  },
]

export function TaskCardStack({
  tasks: initialTasks,
  onApply,
  onIgnore,
}: {
  tasks?: Task[]
  onApply?: (id: string | number) => Promise<void> | void
  onIgnore?: (id: string | number) => Promise<void> | void
}) {
  const [tasks, setTasks] = useState<Task[]>(initialTasks ?? sampleTasks)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [direction, setDirection] = useState<"left" | "right" | null>(null)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const cardRef = useRef<HTMLDivElement>(null)

  const currentTask = tasks[currentIndex]

  const handleSwipe = async (swipeDirection: "left" | "right") => {
  setDirection(swipeDirection);

  setTimeout(async () => {
    const current = tasks[currentIndex];

    if (swipeDirection === "right" && onApply) {
      await onApply(current.id);   // FIX: await instead of fire-and-forget
    }

    if (swipeDirection === "left" && onIgnore) {
      await onIgnore(current.id);  // FIX: await instead of void
    }

    // Move to next card
    if (currentIndex < tasks.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      setCurrentIndex(0);
    }

    setDirection(null);
    setDragOffset({ x: 0, y: 0 });
    setIsDragging(false);
  }, 300)
}


  const handleDragStart = (clientX: number, clientY: number) => {
    setIsDragging(true)
    setDragStart({ x: clientX, y: clientY })
  }

  const handleDragMove = (clientX: number, clientY: number) => {
    if (!isDragging) return

    const offsetX = clientX - dragStart.x
    const offsetY = clientY - dragStart.y
    setDragOffset({ x: offsetX, y: offsetY })
  }

  const handleDragEnd = () => {
    if (!isDragging) return

    const swipeThreshold = 100 // pixels to trigger swipe

    if (Math.abs(dragOffset.x) > swipeThreshold) {
      if (dragOffset.x > 0) {
        handleSwipe("right")
      } else {
        handleSwipe("left")
      }
    } else {
      // Reset position if not swiped far enough
      setDragOffset({ x: 0, y: 0 })
      setIsDragging(false)
    }
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    handleDragStart(e.clientX, e.clientY)
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    handleDragMove(e.clientX, e.clientY)
  }

  const handleMouseUp = () => {
    handleDragEnd()
  }

  const handleTouchStart = (e: React.TouchEvent) => {
    const touch = e.touches[0]
    handleDragStart(touch.clientX, touch.clientY)
  }

  const handleTouchMove = (e: React.TouchEvent) => {
    const touch = e.touches[0]
    handleDragMove(touch.clientX, touch.clientY)
  }

  const handleTouchEnd = () => {
    handleDragEnd()
  }

  const handleIgnore = () => {
    handleSwipe("left")
  }

  const handleApply = () => {
    handleSwipe("right")
  }

  if (!currentTask) {
    return (
      <div className="flex flex-col items-center justify-center h-[650px] text-center">
        <p className="text-xl text-muted-foreground mb-4">{"No more tasks available"}</p>
        <Button onClick={() => setCurrentIndex(0)}>Restart</Button>
      </div>
    )
  }

  const rotation = dragOffset.x / 20
  const opacity = 1 - Math.abs(dragOffset.x) / 300

  return (
    <div className="relative">
      <div className="relative h-[650px] mb-6">
        {tasks[currentIndex + 1] && (
          <div className="absolute inset-0 scale-95 opacity-50 pointer-events-none">
            <TaskCard task={tasks[currentIndex + 1]} />
          </div>
        )}

        <div
          ref={cardRef}
          className={`absolute inset-0 cursor-grab active:cursor-grabbing select-none touch-none ${
            direction === "left"
              ? "-translate-x-[150%] rotate-[-30deg] opacity-0"
              : direction === "right"
                ? "translate-x-[150%] rotate-[30deg] opacity-0"
                : ""
          }`}
          style={{
            transform: !direction
              ? `translateX(${dragOffset.x}px) translateY(${dragOffset.y}px) rotate(${rotation}deg)`
              : undefined,
            opacity: !direction ? opacity : undefined,
            transition: isDragging ? "none" : "all 0.3s",
          }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
        >
          <TaskCard task={currentTask} />

          {isDragging && Math.abs(dragOffset.x) > 50 && (
            <>
              {dragOffset.x > 0 && (
                <div className="absolute top-12 right-12 border-4 border-green-500 text-green-500 px-6 py-3 rounded-lg font-bold text-2xl rotate-[20deg] shadow-lg">
                  APPLY
                </div>
              )}
              {dragOffset.x < 0 && (
                <div className="absolute top-12 left-12 border-4 border-red-500 text-red-500 px-6 py-3 rounded-lg font-bold text-2xl -rotate-[20deg] shadow-lg">
                  NOPE
                </div>
              )}
            </>
          )}
        </div>
      </div>

      <div className="flex items-center justify-center gap-4">
        <Button
          size="lg"
          variant="outline"
          className="h-14 w-14 rounded-full border-2 hover:scale-110 transition-transform bg-white shadow-md"
          onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
          disabled={currentIndex === 0}
        >
          <RotateCcw className="h-6 w-6 text-yellow-500" />
          <span className="sr-only">Undo</span>
        </Button>

        <Button
          size="lg"
          variant="outline"
          className="h-16 w-16 rounded-full border-2 hover:scale-110 transition-transform bg-white shadow-md"
          onClick={handleIgnore}
        >
          <X className="h-8 w-8 text-red-500" />
          <span className="sr-only">Ignore</span>
        </Button>

        <Button
          size="lg"
          className="h-14 w-14 rounded-full hover:scale-110 transition-transform bg-blue-500 hover:bg-blue-600 text-white shadow-lg"
        >
          <Star className="h-6 w-6 fill-current" />
          <span className="sr-only">Super Apply</span>
        </Button>

        <Button
          size="lg"
          className="h-16 w-16 rounded-full hover:scale-110 transition-transform bg-green-500 hover:bg-green-600 text-white shadow-lg"
          onClick={handleApply}
        >
          <Check className="h-8 w-8 stroke-[3]" />
          <span className="sr-only">Apply</span>
        </Button>

        <Button
          size="lg"
          variant="outline"
          className="h-14 w-14 rounded-full border-2 hover:scale-110 transition-transform bg-white shadow-md"
        >
          <Star className="h-6 w-6 text-purple-500" />
          <span className="sr-only">Boost</span>
        </Button>
      </div>

      <div className="text-center mt-6 text-sm text-muted-foreground">
        {currentIndex + 1} / {tasks.length}
      </div>
    </div>
  )
}

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { MapPin, DollarSign, User } from "lucide-react"

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

interface TaskCardProps {
  task: Task
}

export function TaskCard({ task }: TaskCardProps) {
  return (
    <Card className="h-full w-full shadow-xl overflow-hidden relative border-0">
      <div className="absolute inset-0 z-0">
        <img src={task.coverImage || "/placeholder.svg"} alt={task.title} className="h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/90" />
      </div>

      <div className="relative z-10 flex flex-col h-full justify-end p-6 pb-8">
        <div className="space-y-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-3xl font-bold text-white drop-shadow-lg">{task.title}</h2>
              <Badge className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-md">
                {task.category}
              </Badge>
            </div>
            <p className="text-base text-white/95 leading-relaxed text-pretty drop-shadow mb-4">{task.description}</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 bg-white/20 backdrop-blur-md rounded-full px-4 py-2">
              <DollarSign className="h-4 w-4 text-white" />
              <span className="text-sm font-semibold text-white">{task.reward}</span>
            </div>

            <div className="flex items-center gap-2 bg-white/20 backdrop-blur-md rounded-full px-4 py-2">
              <User className="h-4 w-4 text-white" />
              <span className="text-sm font-medium text-white">{task.postedBy}</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function MarketSkeleton() {
  return (
    <div className="flex-1 flex flex-col gap-20 max-w-6xl w-full p-5">
      <main className="flex-1 flex flex-col gap-6 px-0">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-96" />
        
        <div className="flex flex-col gap-4">
        {/* Filter Section Skeleton */}
        <Card className="p-4">
          <div className="flex items-center justify-between mb-3">
            <Skeleton className="h-6 w-32" />
          </div>
          
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-10 w-full" />
            </div>
            
            <div className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-10 w-full" />
            </div>
            
            <div className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-10 w-full" />
            </div>
          </div>
        </Card>

        {/* Tabs Skeleton */}
        <div className="flex gap-2 border-b">
          <Skeleton className="h-10 w-32" />
          <Skeleton className="h-10 w-32" />
        </div>

        {/* Listings Grid Skeleton */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="overflow-hidden">
              <Skeleton className="h-48 w-full" />
              <div className="p-4 space-y-3">
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
                
                <div className="flex flex-wrap gap-2 mt-3">
                  <Skeleton className="h-5 w-16" />
                  <Skeleton className="h-5 w-20" />
                  <Skeleton className="h-5 w-14" />
                </div>
                
                <div className="flex items-center justify-between pt-3">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-9 w-20" />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
      </main>
    </div>
  );
}

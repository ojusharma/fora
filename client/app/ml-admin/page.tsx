"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function MLAdminPage() {
  const [training, setTraining] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string>("");

  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  async function handleGenerateSampleData() {
    setGenerating(true);
    setError("");
    setStatus("Generating sample data...");

    try {
      const response = await fetch(`${baseUrl}/api/v1/admin/generate-sample-data`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Failed to generate sample data");
      }

      const data = await response.json();
      setStatus(`✓ Generated sample data: ${JSON.stringify(data)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate sample data");
      setStatus("");
    } finally {
      setGenerating(false);
    }
  }

  async function handleTriggerTraining(type: "daily" | "hourly" | "frequent") {
    setTraining(true);
    setError("");
    setStatus(`Running ${type} training tasks...`);

    try {
      const response = await fetch(`${baseUrl}/api/v1/admin/train-ml`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ task_type: type }),
      });

      if (!response.ok) {
        throw new Error(`Failed to trigger ${type} training`);
      }

      const data = await response.json();
      setStatus(`✓ ${type.charAt(0).toUpperCase() + type.slice(1)} training completed: ${data.message || "Success"}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to trigger ${type} training`);
      setStatus("");
    } finally {
      setTraining(false);
    }
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold">ML Admin Panel</h1>
          <p className="text-muted-foreground mt-2">
            Development tools for managing the ML recommendation engine
          </p>
          <Badge variant="outline" className="mt-2">
            🔧 Dev Only
          </Badge>
        </div>

        {status && (
          <Card className="bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
            <CardContent className="py-4">
              <p className="text-sm text-green-800 dark:text-green-200">{status}</p>
            </CardContent>
          </Card>
        )}

        {error && (
          <Card className="bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800">
            <CardContent className="py-4">
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Generate Sample Data</CardTitle>
            <CardDescription>
              Create sample listings and interactions to bootstrap the ML system
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              This will create 20-30 sample listings with various tags and fake user interactions.
              Use this to test the recommendation system.
            </p>
            <Button
              onClick={handleGenerateSampleData}
              disabled={generating}
              size="lg"
            >
              {generating ? "Generating..." : "Generate Sample Data"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Manual Training Triggers</CardTitle>
            <CardDescription>
              Manually trigger ML training tasks (normally run on schedule)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-3">
              <div>
                <h3 className="font-semibold mb-1">Daily Training</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Computes user similarity matrices and feature vectors (normally runs at 2 AM)
                </p>
                <Button
                  onClick={() => handleTriggerTraining("daily")}
                  disabled={training}
                  variant="outline"
                >
                  {training ? "Training..." : "Run Daily Training"}
                </Button>
              </div>

              <div>
                <h3 className="font-semibold mb-1">Hourly Updates</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Updates engagement metrics and trending scores (normally runs every hour)
                </p>
                <Button
                  onClick={() => handleTriggerTraining("hourly")}
                  disabled={training}
                  variant="outline"
                >
                  {training ? "Updating..." : "Run Hourly Update"}
                </Button>
              </div>

              <div>
                <h3 className="font-semibold mb-1">Frequent Updates</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Refreshes trending listings view (normally runs every 15 minutes)
                </p>
                <Button
                  onClick={() => handleTriggerTraining("frequent")}
                  disabled={training}
                  variant="outline"
                >
                  {training ? "Refreshing..." : "Run Frequent Update"}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Setup Guide</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p><strong>Step 1:</strong> Generate sample data (if you don&apos;t have listings)</p>
            <p><strong>Step 2:</strong> Run daily training to compute user similarities</p>
            <p><strong>Step 3:</strong> Run hourly update to calculate engagement scores</p>
            <p><strong>Step 4:</strong> Visit the home page to see recommendations!</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

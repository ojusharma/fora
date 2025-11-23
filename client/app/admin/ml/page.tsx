"use client";

import { useState } from "react";
import { useAdmin } from "@/hooks/use-admin";
import { AdminGuard } from "@/components/admin/admin-guard";
import { AdminNav } from "@/components/admin/admin-nav";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function AdminMLPage() {
  const { triggerMLTraining, generateSampleData, loading, error } = useAdmin();
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [trainingStatus, setTrainingStatus] = useState<{
    [key: string]: "idle" | "loading" | "success" | "error";
  }>({
    daily: "idle",
    hourly: "idle",
    frequent: "idle",
    sampleData: "idle",
  });

  const handleTriggerTraining = async (taskType: "daily" | "hourly" | "frequent") => {
    setSuccessMessage(null);
    setTrainingStatus((prev) => ({ ...prev, [taskType]: "loading" }));

    try {
      const result = await triggerMLTraining(taskType);
      setTrainingStatus((prev) => ({ ...prev, [taskType]: "success" }));
      setSuccessMessage(result.message || "Training completed successfully");

      // Reset status after 3 seconds
      setTimeout(() => {
        setTrainingStatus((prev) => ({ ...prev, [taskType]: "idle" }));
      }, 3000);
    } catch (err) {
      setTrainingStatus((prev) => ({ ...prev, [taskType]: "error" }));
      console.error("Training failed:", err);

      // Reset status after 3 seconds
      setTimeout(() => {
        setTrainingStatus((prev) => ({ ...prev, [taskType]: "idle" }));
      }, 3000);
    }
  };

  const handleGenerateSampleData = async () => {
    setSuccessMessage(null);
    setTrainingStatus((prev) => ({ ...prev, sampleData: "loading" }));

    try {
      const result = await generateSampleData();
      setTrainingStatus((prev) => ({ ...prev, sampleData: "success" }));
      setSuccessMessage(
        `Sample data generated: ${result.listings_created} listings, ${result.interactions_created} interactions`
      );

      // Reset status after 3 seconds
      setTimeout(() => {
        setTrainingStatus((prev) => ({ ...prev, sampleData: "idle" }));
      }, 3000);
    } catch (err) {
      setTrainingStatus((prev) => ({ ...prev, sampleData: "error" }));
      console.error("Sample data generation failed:", err);

      // Reset status after 3 seconds
      setTimeout(() => {
        setTrainingStatus((prev) => ({ ...prev, sampleData: "idle" }));
      }, 3000);
    }
  };

  const getButtonVariant = (status: string) => {
    if (status === "success") return "default";
    if (status === "error") return "destructive";
    return "outline";
  };

  const getButtonText = (status: string, defaultText: string) => {
    if (status === "loading") return "Running...";
    if (status === "success") return "Success";
    if (status === "error") return "Failed";
    return defaultText;
  };

  return (
    <AdminGuard>
      <div className="min-h-screen bg-black text-white">
        <div className="container mx-auto py-8 px-4 max-w-7xl">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">ML Training Management</h1>
              <p className="text-gray-400">
                Trigger machine learning training tasks and manage test data
              </p>
            </div>
            <Link href="/">
              <Button variant="outline" className="border-gray-700 text-white hover:bg-gray-800">
                Back to Home
              </Button>
            </Link>
          </div>

          <AdminNav />

        {error && (
          <div className="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 px-4 py-3 rounded mb-6">
            <p className="font-medium">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {successMessage && (
          <div className="bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800 text-green-800 dark:text-green-200 px-4 py-3 rounded mb-6">
            <p className="font-medium">Success</p>
            <p className="text-sm">{successMessage}</p>
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
          {/* Daily Training */}
          <Card>
            <CardHeader>
              <CardTitle>
                Daily Training
              </CardTitle>
              <CardDescription>
                Compute user similarity matrices and feature vectors
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  This task runs comprehensive ML training including:
                </p>
                <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                  <li>User similarity matrix computation</li>
                  <li>User feature vector updates</li>
                  <li>Collaborative filtering model training</li>
                </ul>
                <p className="text-xs text-muted-foreground mt-3">
                  Normally runs: Daily at 2:00 AM UTC
                </p>
                <Button
                  className="w-full mt-4"
                  variant={getButtonVariant(trainingStatus.daily)}
                  onClick={() => handleTriggerTraining("daily")}
                  disabled={trainingStatus.daily === "loading"}
                >
                  {getButtonText(trainingStatus.daily, "Run Daily Training")}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Hourly Updates */}
          <Card>
            <CardHeader>
              <CardTitle>
                Hourly Updates
              </CardTitle>
              <CardDescription>
                Update engagement scores and metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  This task performs incremental updates:
                </p>
                <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                  <li>Listing engagement score updates</li>
                  <li>User interaction metrics refresh</li>
                  <li>Real-time recommendation adjustments</li>
                </ul>
                <p className="text-xs text-muted-foreground mt-3">
                  Normally runs: Every hour
                </p>
                <Button
                  className="w-full mt-4"
                  variant={getButtonVariant(trainingStatus.hourly)}
                  onClick={() => handleTriggerTraining("hourly")}
                  disabled={trainingStatus.hourly === "loading"}
                >
                  {getButtonText(trainingStatus.hourly, "Run Hourly Update")}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Frequent Updates */}
          <Card>
            <CardHeader>
              <CardTitle>
                Frequent Updates
              </CardTitle>
              <CardDescription>
                Refresh trending listings and quick metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  This task handles rapid updates:
                </p>
                <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                  <li>Trending listings refresh</li>
                  <li>Real-time popularity scores</li>
                  <li>Quick interaction metrics</li>
                </ul>
                <p className="text-xs text-muted-foreground mt-3">
                  Normally runs: Every 15 minutes
                </p>
                <Button
                  className="w-full mt-4"
                  variant={getButtonVariant(trainingStatus.frequent)}
                  onClick={() => handleTriggerTraining("frequent")}
                  disabled={trainingStatus.frequent === "loading"}
                >
                  {getButtonText(trainingStatus.frequent, "Run Frequent Update")}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Generate Sample Data */}
          <Card>
            <CardHeader>
              <CardTitle>
                Generate Sample Data
              </CardTitle>
              <CardDescription>
                Create test listings and interactions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  Useful for testing and development:
                </p>
                <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                  <li>Creates 20-30 sample listings</li>
                  <li>Generates user interactions</li>
                  <li>Bootstraps ML system with test data</li>
                </ul>
                <div className="bg-yellow-50 dark:bg-yellow-900/10 border border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-200 px-3 py-2 rounded text-xs mt-3">
                  Warning: Use this only in development environments
                </div>
                <Button
                  className="w-full mt-4"
                  variant={getButtonVariant(trainingStatus.sampleData)}
                  onClick={handleGenerateSampleData}
                  disabled={trainingStatus.sampleData === "loading"}
                >
                  {getButtonText(trainingStatus.sampleData, "Generate Sample Data")}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Information Card */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>About ML Training</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <h4 className="font-medium mb-2">Automated Schedule</h4>
              <p className="text-sm text-muted-foreground">
                The ML training tasks run automatically according to their schedules. Use these
                manual triggers only when you need to:
              </p>
              <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside mt-2">
                <li>Test the training system</li>
                <li>Force an immediate update after major changes</li>
                <li>Troubleshoot recommendation issues</li>
                <li>Bootstrap the system with initial data</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">Performance Impact</h4>
              <p className="text-sm text-muted-foreground">
                Daily training can take several minutes depending on the amount of data. Hourly
                and frequent updates are faster. Consider the current platform load before
                triggering manual training.
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-2">Monitoring</h4>
              <p className="text-sm text-muted-foreground">
                Check your server logs for detailed training progress and any errors that occur
                during the ML training process.
              </p>
            </div>
          </CardContent>
        </Card>
        </div>
      </div>
    </AdminGuard>
  );
}

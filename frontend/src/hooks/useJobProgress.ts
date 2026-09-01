import { useState, useEffect } from "react";
import { JobWebSocketClient, JobProgressEvent } from "../api/ws";

export function useJobProgress(jobId?: string) {
  const [progress, setProgress] = useState<JobProgressEvent | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isCompleted, setIsCompleted] = useState<boolean>(false);
  const [isFailed, setIsFailed] = useState<boolean>(false);

  useEffect(() => {
    if (!jobId) return;

    const ws = new JobWebSocketClient(
      jobId,
      (event) => {
        setProgress(event);
        if (event.status === "complete") {
          setIsCompleted(true);
        } else if (event.status === "failed") {
          setIsFailed(true);
        }
      },
      {
        onOpen: () => setIsConnected(true),
        onClose: () => setIsConnected(false),
        onError: () => setIsConnected(false),
      }
    );

    ws.connect();

    return () => {
      ws.disconnect();
    };
  }, [jobId]);

  return {
    progress,
    isConnected,
    isCompleted,
    isFailed,
  };
}

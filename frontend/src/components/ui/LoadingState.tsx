import React from "react";
import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = "Loading system state...",
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center min-h-[200px]">
      <Loader2 className="w-8 h-8 text-accent animate-spin mb-3" />
      <p className="text-text-secondary text-sm font-medium">{message}</p>
    </div>
  );
};

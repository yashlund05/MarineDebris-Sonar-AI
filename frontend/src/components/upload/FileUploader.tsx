import React, { useState } from "react";
import { useDropzone } from "react-dropzone";
import {
  UploadCloud,
  FileCheck,
  AlertCircle,
  FileType,
  Compass,
  ArrowRight,
  Loader2,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { surveysApi } from "../../api/surveys";

export const FileUploader: React.FC = () => {
  const navigate = useNavigate();

  const [sonarFile, setSonarFile] = useState<File | null>(null);
  const [navFile, setNavFile] = useState<File | null>(null);
  const [channel, setChannel] = useState<string>("starboard");
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const onDropSonar = (acceptedFiles: File[]) => {
    setErrorMessage(null);
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      const ext = file.name.split(".").pop()?.toLowerCase();
      const validExtensions = ["xtf", "jsf", "png", "tif", "tiff"];
      if (!ext || !validExtensions.includes(ext)) {
        setErrorMessage(
          `Unsupported format '.${ext}'. Supported formats: .xtf, .jsf, .png, .tif, .tiff`
        );
        return;
      }
      if (file.size > 2048 * 1024 * 1024) {
        setErrorMessage("File exceeds the 2 GB maximum upload limit.");
        return;
      }
      setSonarFile(file);
    }
  };

  const onDropNav = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setNavFile(acceptedFiles[0]);
    }
  };

  const {
    getRootProps: getSonarRootProps,
    getInputProps: getSonarInputProps,
    isDragActive: isSonarDragActive,
  } = useDropzone({
    onDrop: onDropSonar,
    maxFiles: 1,
    multiple: false,
  });

  const {
    getRootProps: getNavRootProps,
    getInputProps: getNavInputProps,
    isDragActive: isNavDragActive,
  } = useDropzone({
    onDrop: onDropNav,
    maxFiles: 1,
    multiple: false,
    accept: { "text/csv": [".csv"] },
  });

  const handleUpload = async () => {
    if (!sonarFile) {
      setErrorMessage("Please select a sonar file to upload.");
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setErrorMessage(null);

    try {
      const response = await surveysApi.uploadSurvey(
        sonarFile,
        navFile || undefined,
        channel,
        (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percent);
          }
        }
      );

      if (response.success && response.data) {
        navigate(`/surveys/${response.data.survey_id}`);
      }
    } catch (err: any) {
      const msg =
        err.response?.data?.error?.message ||
        err.message ||
        "Upload failed. Please check backend connection.";
      setErrorMessage(msg);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Main Sonar File Dropzone */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 space-y-4">
        <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
          <FileType className="w-4 h-4 text-accent" />
          1. Select Sonar Survey File (Required)
        </h3>

        <div
          {...getSonarRootProps()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
            isSonarDragActive
              ? "border-accent bg-accent/5 scale-[1.01]"
              : sonarFile
              ? "border-emerald-500/40 bg-emerald-500/5"
              : "border-border-subtle hover:border-accent/40 bg-bg-elevated/40"
          }`}
        >
          <input {...getSonarInputProps()} />

          {sonarFile ? (
            <div className="flex flex-col items-center space-y-2 text-emerald-400">
              <FileCheck className="w-10 h-10" />
              <p className="font-medium text-sm text-text-primary">{sonarFile.name}</p>
              <p className="font-mono text-xs text-text-secondary">
                {(sonarFile.size / (1024 * 1024)).toFixed(2)} MB
              </p>
              <span className="text-xs text-accent underline pt-2">
                Click or drop another file to replace
              </span>
            </div>
          ) : (
            <div className="flex flex-col items-center space-y-3">
              <div className="p-3 bg-bg-elevated rounded-full text-accent">
                <UploadCloud className="w-8 h-8" />
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">
                  Drag and drop your sonar record here, or{" "}
                  <span className="text-accent underline">browse</span>
                </p>
                <p className="text-xs text-text-secondary mt-1">
                  Supported formats: <span className="font-mono font-medium">.xtf</span>,{" "}
                  <span className="font-mono font-medium">.png</span> (MVP) |{" "}
                  <span className="font-mono text-text-muted">.jsf, .tif, .tiff</span> (V1)
                </p>
              </div>
              <p className="text-[11px] text-text-muted">Maximum file size: 2 GB</p>
            </div>
          )}
        </div>
      </div>

      {/* Auxiliary Navigation CSV Dropzone (Optional) */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
            <Compass className="w-4 h-4 text-cyan-400" />
            2. Auxiliary Navigation CSV (Optional)
          </h3>
          <span className="text-xs text-text-muted">Required for PNG georeferencing</span>
        </div>

        <div
          {...getNavRootProps()}
          className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all duration-200 ${
            isNavDragActive
              ? "border-cyan-400 bg-cyan-400/5"
              : navFile
              ? "border-emerald-500/40 bg-emerald-500/5"
              : "border-border-subtle hover:border-cyan-400/40 bg-bg-elevated/40"
          }`}
        >
          <input {...getNavInputProps()} />
          {navFile ? (
            <div className="flex items-center justify-center gap-3 text-emerald-400">
              <FileCheck className="w-5 h-5" />
              <span className="text-sm text-text-primary font-medium">{navFile.name}</span>
              <span className="text-xs text-text-secondary font-mono">
                ({(navFile.size / 1024).toFixed(1)} KB)
              </span>
            </div>
          ) : (
            <p className="text-xs text-text-secondary">
              Drop external navigation CSV with ping_number, timestamp, lat, lon, heading, altitude.
            </p>
          )}
        </div>
      </div>

      {/* Channel and Settings */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <label className="text-xs font-semibold text-text-primary">Sonar Channel</label>
          <p className="text-xs text-text-secondary">
            Select swath channel for processing
          </p>
        </div>

        <div className="flex items-center gap-2">
          {["starboard", "port", "both"].map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setChannel(c)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium capitalize transition-all ${
                channel === c
                  ? "bg-accent text-white font-semibold"
                  : "bg-bg-elevated text-text-secondary hover:text-text-primary"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Error Message */}
      {errorMessage && (
        <div className="p-4 bg-red-950/40 border border-red-500/40 rounded-xl flex items-center gap-3 text-red-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Upload Progress */}
      {isUploading && (
        <div className="p-4 bg-bg-surface border border-border-subtle rounded-xl space-y-2">
          <div className="flex items-center justify-between text-xs font-medium">
            <span className="flex items-center gap-2 text-accent">
              <Loader2 className="w-4 h-4 animate-spin" />
              Uploading survey to server storage...
            </span>
            <span className="font-mono text-text-primary">{uploadProgress}%</span>
          </div>
          <div className="w-full bg-bg-elevated h-2 rounded-full overflow-hidden">
            <div
              className="bg-accent h-full transition-all duration-200 rounded-full"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Submit Button */}
      <div className="flex justify-end">
        <button
          type="button"
          onClick={handleUpload}
          disabled={!sonarFile || isUploading}
          className="inline-flex items-center gap-2 px-6 py-3 bg-accent hover:bg-accent-hover text-white text-sm font-semibold rounded-xl transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          {isUploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Processing Upload...
            </>
          ) : (
            <>
              Start Automated AI Inspection
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
};

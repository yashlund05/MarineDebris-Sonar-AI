import React, { useState, useEffect } from "react";
import {
  UploadCloud,
  Download,
  SplitSquareVertical,
  Columns,
  RefreshCw,
  FileImage,
} from "lucide-react";
import { BeforeAfterSlider } from "./BeforeAfterSlider";
import { SideBySideViewer } from "./SideBySideViewer";
import { EnhancementControls } from "./EnhancementControls";
import { QualityDiagnosticsCard } from "./QualityDiagnosticsCard";
import {
  EnhancementResponse,
  SonarEnhancementConfig,
  PaletteItem,
  SampleItem,
} from "../../types/sonarEnhancement";
import { sonarEnhancementApi } from "../../api/sonarEnhancement";

export const SonarEnhancementWorkbench: React.FC = () => {
  const [viewMode, setViewMode] = useState<"slider" | "side-by-side">("slider");
  const [displayMode, setDisplayMode] = useState<"pseudocolor" | "grayscale">("pseudocolor");
  const [showDetections, setShowDetections] = useState<boolean>(true);

  const [palettes, setPalettes] = useState<PaletteItem[]>([]);
  const [samples, setSamples] = useState<SampleItem[]>([]);
  const [selectedSample, setSelectedSample] = useState<string>("");

  // Track active uploaded file so re-applying filters never switches image
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string>("");

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EnhancementResponse | null>(null);

  const [config, setConfig] = useState<SonarEnhancementConfig>({
    convert_to_db: true,
    stripe_noise_filter: true,
    clahe: true,
    clahe_clip_limit: 0.01,
    sharpening: false,
    sharpening_gamma_h: 2.0,
    sharpening_gamma_l: 0.5,
    sharpening_c: 1.5,
    gain_normalization: false,
    colormap: "amber",
    run_detection: false,
    conf_threshold: 0.25,
    detection_input_mode: "enhanced_grayscale",
  });

  // Load initial palettes & samples
  useEffect(() => {
    const fetchInit = async () => {
      try {
        const [palettesRes, samplesRes] = await Promise.all([
          sonarEnhancementApi.getPalettes(),
          sonarEnhancementApi.getSamples("v3", "val"),
        ]);
        if (palettesRes.success) setPalettes(palettesRes.palettes);
        if (samplesRes.success && samplesRes.samples.length > 0) {
          setSamples(samplesRes.samples);
          setSelectedSample(samplesRes.samples[0].name);
        }
      } catch (err: any) {
        console.error("Failed to load palettes or samples:", err);
      }
    };
    fetchInit();
  }, []);

  // Run initial enhancement when sample is resolved
  useEffect(() => {
    if (selectedSample && selectedSample !== "__custom_upload__") {
      handleEnhance(selectedSample);
    }
  }, [selectedSample]);

  const handleEnhance = async (sampleName?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      let res: EnhancementResponse;

      // 1. If currently working on an uploaded file and not switching to a dataset sample
      if (uploadedFile && (!sampleName || sampleName === "__custom_upload__")) {
        res = await sonarEnhancementApi.enhanceUploadedFile(uploadedFile, config);
      } else {
        // 2. Working on dataset sample or anchored image
        const targetSample = sampleName || (selectedSample !== "__custom_upload__" ? selectedSample : "");
        const payload: any = {
          ...config,
          dataset_version: "v3",
          split: "val",
        };
        if (targetSample) {
          payload.image_name = targetSample;
        }
        // Anchor to current raw image data URL if available so frame NEVER changes on re-filtering
        if (result?.raw_image_data_url) {
          payload.image_data_url = result.raw_image_data_url;
        }
        res = await sonarEnhancementApi.enhanceImage(payload);
      }
      setResult(res);
    } catch (err: any) {
      setError(err?.message || "Enhancement pipeline failed to process image.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadedFile(file);
    setUploadedFileName(file.name);
    setSelectedSample("__custom_upload__");

    setIsLoading(true);
    setError(null);
    try {
      const res = await sonarEnhancementApi.enhanceUploadedFile(file, config);
      setResult(res);
    } catch (err: any) {
      setError(err?.message || "Failed to enhance uploaded image.");
    } finally {
      setIsLoading(false);
      // Reset input value so user can re-select same file if desired
      e.target.value = "";
    }
  };

  const handleRecolorFast = async (paletteId: string) => {
    if (!result?.cache_key) return;
    try {
      const recolorRes = await sonarEnhancementApi.recolorCachedFrame(result.cache_key, paletteId);
      if (recolorRes.success) {
        setResult((prev) => (prev ? {
          ...prev,
          colormap: paletteId,
          pseudocolor_data_url: recolorRes.pseudocolor_data_url,
        } : null));
      }
    } catch (err) {
      console.error("Fast recoloring failed:", err);
    }
  };

  const handleConfigChange = (updated: Partial<SonarEnhancementConfig>) => {
    setConfig((prev) => ({ ...prev, ...updated }));
  };

  const activeFrameLabel = uploadedFileName || result?.source_filename || selectedSample || "Sonar Frame";

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Controls Toolbar */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
        {/* Left: Sample picker & Upload */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs">
            <span className="font-semibold text-text-primary">Source:</span>
            <select
              value={uploadedFileName ? "__custom_upload__" : selectedSample}
              onChange={(e) => {
                const val = e.target.value;
                if (val !== "__custom_upload__") {
                  setUploadedFile(null);
                  setUploadedFileName("");
                  setSelectedSample(val);
                }
              }}
              disabled={isLoading}
              className="px-3 py-1.5 bg-bg-elevated border border-border-subtle rounded-xl text-xs font-mono text-text-primary focus:ring-accent focus:border-accent max-w-[240px] truncate"
            >
              {uploadedFileName && (
                <option value="__custom_upload__">
                  📁 Upload: {uploadedFileName}
                </option>
              )}
              {samples.map((s) => (
                <option key={s.name} value={s.name}>
                  {s.name} {s.has_annotations ? `(${s.box_count} objs)` : ""}
                </option>
              ))}
            </select>
          </div>

          <label className="flex items-center gap-1.5 px-3 py-1.5 bg-bg-elevated hover:bg-bg-subtle text-text-secondary text-xs font-medium rounded-xl border border-border-subtle cursor-pointer transition">
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Upload Frame</span>
            <input
              type="file"
              accept=".png,.jpg,.jpeg,.tif,.tiff"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>

          {/* Active Image Indicator Badge */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-accent-subtle/30 text-accent rounded-xl text-xs font-mono border border-accent/20">
            <FileImage className="w-3.5 h-3.5" />
            <span className="max-w-[160px] truncate font-medium">{activeFrameLabel}</span>
          </div>
        </div>

        {/* Center: View Switcher & Display Mode */}
        <div className="flex items-center gap-2">
          {/* Detection Bounding Box Toggle (when available) */}
          {result?.detection_results && (
            <label className="flex items-center gap-1.5 px-2.5 py-1 bg-bg-elevated rounded-xl border border-border-subtle text-xs cursor-pointer select-none">
              <input
                type="checkbox"
                checked={showDetections}
                onChange={(e) => setShowDetections(e.target.checked)}
                className="w-3.5 h-3.5 text-accent rounded focus:ring-accent"
              />
              <span className="text-text-secondary">Detections ({result.detection_results.detection_count})</span>
            </label>
          )}

          {/* Slider vs Side-by-Side */}
          <div className="bg-bg-elevated p-1 rounded-xl flex items-center border border-border-subtle text-xs">
            <button
              type="button"
              onClick={() => setViewMode("slider")}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg transition font-medium ${
                viewMode === "slider"
                  ? "bg-bg-surface text-text-primary shadow-sm"
                  : "text-text-muted hover:text-text-primary"
              }`}
            >
              <SplitSquareVertical className="w-3.5 h-3.5" />
              <span>Split Slider</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("side-by-side")}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg transition font-medium ${
                viewMode === "side-by-side"
                  ? "bg-bg-surface text-text-primary shadow-sm"
                  : "text-text-muted hover:text-text-primary"
              }`}
            >
              <Columns className="w-3.5 h-3.5" />
              <span>Side by Side</span>
            </button>
          </div>

          {/* False-Color vs Grayscale */}
          <div className="bg-bg-elevated p-1 rounded-xl flex items-center border border-border-subtle text-xs">
            <button
              type="button"
              onClick={() => setDisplayMode("pseudocolor")}
              className={`px-2.5 py-1 rounded-lg transition font-medium ${
                displayMode === "pseudocolor"
                  ? "bg-bg-surface text-accent shadow-sm font-semibold"
                  : "text-text-muted hover:text-text-primary"
              }`}
            >
              False-Color
            </button>
            <button
              type="button"
              onClick={() => setDisplayMode("grayscale")}
              className={`px-2.5 py-1 rounded-lg transition font-medium ${
                displayMode === "grayscale"
                  ? "bg-bg-surface text-text-primary shadow-sm font-semibold"
                  : "text-text-muted hover:text-text-primary"
              }`}
            >
              Grayscale
            </button>
          </div>
        </div>

        {/* Right: Export Downloads */}
        {result && (
          <div className="flex items-center gap-2">
            <a
              href={sonarEnhancementApi.getDownloadUrl(result.cache_key, "pseudocolor")}
              download
              className="flex items-center gap-1.5 px-3 py-1.5 bg-bg-elevated hover:bg-bg-subtle text-text-secondary text-xs font-medium rounded-xl border border-border-subtle transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Pseudocolor</span>
            </a>
            <a
              href={sonarEnhancementApi.getDownloadUrl(result.cache_key, "enhanced_gray")}
              download
              className="flex items-center gap-1.5 px-3 py-1.5 bg-bg-elevated hover:bg-bg-subtle text-text-secondary text-xs font-medium rounded-xl border border-border-subtle transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Grayscale</span>
            </a>
          </div>
        )}
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-600 rounded-2xl text-xs font-medium">
          {error}
        </div>
      )}

      {/* Main Viewport */}
      {result ? (
        viewMode === "slider" ? (
          <BeforeAfterSlider
            key={result.cache_key}
            rawImageUrl={result.raw_image_data_url}
            enhancedImageUrl={result.pseudocolor_data_url}
            enhancedGrayUrl={result.enhanced_grayscale_data_url}
            displayMode={displayMode}
            detections={result.detection_results?.detections}
            showDetections={showDetections}
            rawSha256={result.raw_sha256}
            colormapName={result.colormap}
          />
        ) : (
          <SideBySideViewer
            key={result.cache_key}
            rawImageUrl={result.raw_image_data_url}
            enhancedImageUrl={result.pseudocolor_data_url}
            enhancedGrayUrl={result.enhanced_grayscale_data_url}
            displayMode={displayMode}
            detections={result.detection_results?.detections}
            showDetections={showDetections}
            rawSha256={result.raw_sha256}
            colormapName={result.colormap}
          />
        )
      ) : (
        <div className="w-full h-[400px] rounded-2xl border border-dashed border-border-default bg-bg-elevated/40 flex flex-col items-center justify-center text-text-muted text-xs space-y-2">
          <RefreshCw className={`w-6 h-6 ${isLoading ? "animate-spin text-accent" : ""}`} />
          <span>{isLoading ? "Running SidescanTools Sonar Pipeline..." : "Select or upload a sonar frame to begin"}</span>
        </div>
      )}

      {/* Lower Section: Controls & Quality Diagnostics Grid */}
      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5">
            <EnhancementControls
              config={config}
              onChange={handleConfigChange}
              onApply={() => handleEnhance()}
              onRecolorFast={handleRecolorFast}
              palettes={palettes}
              isLoading={isLoading}
              activeFilename={activeFrameLabel}
            />
          </div>

          <div className="lg:col-span-7">
            <QualityDiagnosticsCard
              metrics={result.metrics}
              auditTrail={result.audit_trail}
              appliedOperations={result.applied_operations}
              executionTimeMs={result.execution_time_ms}
              rawSha256={result.raw_sha256}
            />
          </div>
        </div>
      )}
    </div>
  );
};

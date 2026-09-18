import React, { Suspense, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ArrowUpRight,
  ChevronRight,
  Compass,
  FileSearch,
  Layers3,
  MapPinned,
  Play,
  RadioTower,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  Waves,
} from "lucide-react";
import { surveysApi } from "../api/surveys";
import { systemApi } from "../api/client";

const BathymetryCanvas = React.lazy(() => import("../components/visuals/BathymetryCanvas"));

const statusLabel: Record<string, string> = {
  complete: "Ready for review",
  failed: "Needs attention",
  uploaded: "Awaiting processing",
  queued: "Queued",
  preprocessing: "Preparing signal",
  inferring: "Reading sonar",
  postprocessing: "Verifying targets",
  georeferencing: "Locating findings",
  reporting: "Preparing evidence",
};

export const CommandCenterPage: React.FC = () => {
  const [quietMode, setQuietMode] = useState(false);
  const { data: surveyResponse, isLoading } = useQuery({
    queryKey: ["surveys", "command-center"],
    queryFn: () => surveysApi.getSurveys({ limit: 50 }),
  });
  const { data: health } = useQuery({
    queryKey: ["system-health"],
    queryFn: systemApi.getHealth,
    refetchInterval: 15_000,
    retry: 1,
  });

  const surveys = surveyResponse?.data ?? [];
  const summary = useMemo(() => ({
    active: surveys.filter((survey) => !["complete", "failed"].includes(survey.status)).length,
    review: surveys.filter((survey) => survey.status === "complete").length,
    failed: surveys.filter((survey) => survey.status === "failed").length,
  }), [surveys]);
  const latest = surveys.slice(0, 4);
  const systemLabel = health?.status === "ok" ? "Systems communicating" : health ? "System needs attention" : "Checking systems";

  return (
    <div className="command-center">
      <section className="mission-hero">
        <Suspense fallback={<div className="terrain-canvas mission-scene-fallback" aria-hidden="true" />}>
          <BathymetryCanvas paused={quietMode} className="terrain-canvas" activeCount={summary.active} evidenceCount={summary.review} failedCount={summary.failed} />
        </Suspense>
        <div className="mission-hero__grain" />
        <div className="mission-hero__topline">
          <span><span className="live-dot" /> {systemLabel}</span>
          <button type="button" className="quiet-toggle" onClick={() => setQuietMode((value) => !value)}>
            {quietMode ? <Play size={13} /> : <Waves size={13} />}
            {quietMode ? "Resume scene" : "Pause scene"}
          </button>
        </div>
        <div className="mission-hero__content">
          <p className="eyebrow-light">MarineDebris / acoustic intelligence workstation</p>
          <h1>Evidence, not<br /><em>dashboard theatre.</em></h1>
          <p className="mission-hero__description">
            Follow each uploaded acoustic record from source file to model output, provenance and review. The interactive scene reflects archive state; it is not a geographic or bathymetric claim.
          </p>
          <div className="mission-hero__actions">
            <Link to="/upload" className="hero-primary-action"><Compass size={16} /> Start a new expedition <ArrowUpRight size={15} /></Link>
            <Link to="/surveys" className="hero-secondary-action">Explore survey archive <ChevronRight size={16} /></Link>
          </div>
        </div>
        <div className="mission-hero__coordinate"><span>SOURCE</span> FILE / API MODE<br /><span>LIVE FEED</span> NOT CONNECTED</div>
        <div className="mission-marker"><span /> <div><b>Mission-state scene</b><small>Archive counts only</small></div></div>
      </section>

      <section className="field-strip" aria-label="Current platform summary">
        <div><span>Active expeditions</span><strong>{isLoading ? "—" : summary.active.toString().padStart(2, "0")}</strong><small>Currently in the processing flow</small></div>
        <div><span>Evidence ready</span><strong>{isLoading ? "—" : summary.review.toString().padStart(2, "0")}</strong><small>Completed records in this view</small></div>
        <div><span>Health signal</span><strong className={health?.status === "ok" ? "field-strip__positive" : ""}>{health?.status === "ok" ? "Clear" : health ? "Review" : "Syncing"}</strong><small>{health?.device ? `${health.device.toUpperCase()} inference node` : "Awaiting live telemetry"}</small></div>
        <div><span>Exceptions</span><strong className={summary.failed > 0 ? "field-strip__alert" : ""}>{isLoading ? "—" : summary.failed.toString().padStart(2, "0")}</strong><small>Surveys requiring an operator check</small></div>
      </section>

      <section className="command-grid">
        <article className="expedition-board panel-paper">
          <div className="panel-heading"><div><p className="eyebrow">Field log / newest first</p><h2>Expeditions in view</h2></div><Link to="/surveys">Full archive <ArrowUpRight size={14} /></Link></div>
          {latest.length ? <div className="expedition-list">{latest.map((survey, index) => (
            <Link key={survey.id} to={`/surveys/${survey.id}`} className="expedition-row">
              <span className="expedition-index">{String(index + 1).padStart(2, "0")}</span>
              <span className="expedition-wave"><i /><i /><i /></span>
              <span className="expedition-name"><b>{survey.source_filename}</b><small>{survey.file_type.toUpperCase()} · {new Date(survey.created_at).toLocaleDateString()}</small></span>
              <span className={`status-stamp status-stamp--${survey.status}`}>{statusLabel[survey.status] ?? survey.status}</span>
              <ChevronRight size={16} />
            </Link>
          ))}</div> : <div className="expedition-empty"><Waves size={27} /><h3>Your first expedition begins here.</h3><p>Bring in an XTF or sonar image and the field log, target review, map and exports become available together.</p><Link to="/upload">Begin an expedition <ArrowUpRight size={14} /></Link></div>}
        </article>

        <article className="sonar-window">
          {latest[0] ? <img src={surveysApi.getSonarImageUrl(latest[0].id)} alt={`Sonar evidence for ${latest[0].source_filename}`} /> : null}
          <div className="sonar-window__wash" />
          <div className="sonar-window__header"><span><RadioTower size={14} /> Acoustic evidence</span><span>{latest[0] ? latest[0].file_type.toUpperCase() : "NO SOURCE"}</span></div>
          <div className="sonar-window__annotation"><span className="annotation-dot" /><div><b>{latest[0] ? latest[0].source_filename : "No acoustic evidence selected"}</b><small>{latest[0] ? "This panel only loads a stored survey image; inspect the survey record for detections and provenance." : "Upload a supported record to begin an evidence-backed review."}</small></div></div>
        </article>
      </section>

      <section className="capability-section">
        <div className="capability-intro"><p className="eyebrow">One connected evidence chain</p><h2>From sound to<br /><em>responsible action.</em></h2><p>The platform is structured around an expedition, not a pile of isolated tools. That is what makes it understandable in a demo and useful after one.</p></div>
        <div className="capability-cards">
          <Link to="/upload" className="capability-card capability-card--coral"><span>01 / capture</span><FileSearch size={28} /><h3>Bring the survey in</h3><p>Upload sonar and navigation files with an auditable processing record.</p><b>New expedition <ArrowUpRight size={14} /></b></Link>
          <Link to="/surveys" className="capability-card capability-card--sea"><span>02 / interrogate</span><ScanSearch size={28} /><h3>Read evidence together</h3><p>Sonar, detections, GIS location and processing state stay in one workstation.</p><b>Open field log <ArrowUpRight size={14} /></b></Link>
          <Link to="/models/evaluation" className="capability-card capability-card--sun"><span>03 / govern</span><ShieldCheck size={28} /><h3>Show the model&apos;s work</h3><p>Review performance, stability, lineage and promotion decisions without hiding uncertainty.</p><b>Review intelligence <ArrowUpRight size={14} /></b></Link>
        </div>
      </section>

      <section className="atlas-banner">
        <div className="atlas-banner__map" aria-hidden="true"><span className="map-ring map-ring--one" /><span className="map-ring map-ring--two" /><span className="map-line" /></div>
        <div><p className="eyebrow-light">Next surface / atlas</p><h2>Make every detection<br />belong to a place.</h2></div>
        <div className="atlas-banner__copy"><p>Survey tracks, verified findings and georeferencing quality will be brought together in a navigable 3D spatial atlas.</p><Link to="/surveys">View geographic evidence <MapPinned size={15} /></Link></div>
      </section>

      <section className="research-strip"><span><Sparkles size={15} /> Built for field operators, researchers and coastal stewards</span><Link to="/dataset"><Layers3 size={15} /> Explore dataset provenance <ArrowUpRight size={14} /></Link><Link to="/enhancement"><Activity size={15} /> Open enhancement lab <ArrowUpRight size={14} /></Link></section>
    </div>
  );
};

export default CommandCenterPage;

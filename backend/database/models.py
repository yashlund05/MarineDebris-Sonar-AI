"""SQLAlchemy ORM models conforming strictly to DB_SCHEMA.md."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.types import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Use JSONB on PostgreSQL, standard JSON elsewhere (e.g. SQLite for lightweight tests)
JsonType = JSON().with_variant(JSONB, "postgresql")
UuidType = UUID(as_uuid=True)


class Base(DeclarativeBase):
    """Base declarative class for all models."""
    pass


class Survey(Base):
    """Represents one uploaded sonar file/survey session."""

    __tablename__ = "surveys"

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType,
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    source_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_type: Mapped[str] = mapped_column(String(16), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="uploaded",
        server_default="uploaded",
    )
    channel: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()"),
        onupdate=datetime.utcnow,
    )
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "file_type IN ('xtf', 'jsf', 'png', 'tiff')",
            name="ck_surveys_file_type",
        ),
        CheckConstraint(
            "status IN ('uploaded', 'queued', 'preprocessing', 'inferring', "
            "'postprocessing', 'georeferencing', 'reporting', 'complete', 'failed')",
            name="ck_surveys_status",
        ),
        CheckConstraint(
            "channel IS NULL OR channel IN ('port', 'starboard', 'both', 'unknown')",
            name="ck_surveys_channel",
        ),
        Index("idx_surveys_status", "status"),
        Index("idx_surveys_created_at", text("created_at DESC")),
    )

    # Relationships
    sonar_metadata: Mapped[Optional["SonarMetadata"]] = relationship(
        "SonarMetadata",
        back_populates="survey",
        cascade="all, delete-orphan",
        uselist=False,
    )
    jobs: Mapped[List["ProcessingJob"]] = relationship(
        "ProcessingJob",
        back_populates="survey",
        cascade="all, delete-orphan",
    )
    detections: Mapped[List["Detection"]] = relationship(
        "Detection",
        back_populates="survey",
        cascade="all, delete-orphan",
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="survey",
        cascade="all, delete-orphan",
    )


class SonarMetadata(Base):
    """Navigation and sonar configuration metadata extracted from file header or supplied nav CSV."""

    __tablename__ = "sonar_metadata"

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType,
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    survey_id: Mapped[uuid.UUID] = mapped_column(
        UuidType,
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    frequency_hz: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    samples_per_ping: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_pings: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    range_resolution_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    along_track_resolution_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    survey_start_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    survey_end_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sonar_system: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    motion_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dropout_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    has_attitude_data: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    raw_header: Mapped[Optional[Dict[str, Any]]] = mapped_column(JsonType, nullable=True)

    __table_args__ = (
        UniqueConstraint("survey_id", name="uq_sonar_metadata_survey"),
    )

    # Relationships
    survey: Mapped["Survey"] = relationship("Survey", back_populates="sonar_metadata")


class ProcessingJob(Base):
    """Tracks each pipeline execution for a survey."""

    __tablename__ = "processing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType,
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    survey_id: Mapped[uuid.UUID] = mapped_column(
        UuidType,
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False,
    )
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    progress_pct: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        nullable=True,
        default=0,
        server_default="0",
    )
    current_stage: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    preprocessing_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    detection_model: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    detection_model_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    segmentation_model: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    detection_conf_threshold: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.35,
        server_default="0.35",
    )
    nms_iou_threshold: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.45,
        server_default="0.45",
    )
    tile_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=640,
        server_default="640",
    )
    tile_overlap: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.2,
        server_default="0.2",
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()"),
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'complete', 'failed', 'cancelled')",
            name="ck_processing_jobs_status",
        ),
        CheckConstraint(
            "progress_pct BETWEEN 0 AND 100",
            name="ck_processing_jobs_progress_pct",
        ),
        Index("idx_jobs_survey_id", "survey_id"),
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_celery_task", "celery_task_id"),
    )

    # Relationships
    survey: Mapped["Survey"] = relationship("Survey", back_populates="jobs")
    detections: Mapped[List["Detection"]] = relationship(
        "Detection",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="job",
        cascade="all, delete-orphan",
    )


class Detection(Base):
    """Core table. One row per detected object after NMS and confidence filtering."""

    __tablename__ = "detections"

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType,
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    survey_id: Mapped[uuid.UUID] = mapped_column(
        UuidType,
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UuidType,
        ForeignKey("processing_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    detection_code: Mapped[str] = mapped_column(String(32), nullable=False)
    class_name: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_calibrated: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_x: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_y: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_w: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_h: Mapped[int] = mapped_column(Integer, nullable=False)
    mask_rle: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_length_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_width_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    geotagging_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ping_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ping_timestamp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_filtered: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    filtered_reason: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    source_tile_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JsonType, nullable=True)
    segmentation_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, default="unavailable")
    segmentation_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mask_area: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mask_geometry: Mapped[Optional[Dict[str, Any]]] = mapped_column(JsonType, nullable=True)
    classification_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, default="unavailable")
    classifier_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    classifier_class: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    classifier_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    classification_agreement: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()"),
    )

    __table_args__ = (
        CheckConstraint(
            "class_name IN ("
            "'derelict_fishing_gear', "
            "'general_marine_debris', "
            "'shipwreck', "
            "'pipe_or_cylinder', "
            "'other_man_made_target', "
            "'natural_feature')",
            name="ck_detections_class_name",
        ),
        Index("idx_detections_survey", "survey_id"),
        Index("idx_detections_job", "job_id"),
        Index("idx_detections_class", "class_name"),
        Index("idx_detections_confidence", text("confidence DESC")),
        Index("idx_detections_latlon", "latitude", "longitude"),
        Index("idx_detections_filtered", "is_filtered"),
    )

    # Relationships
    survey: Mapped["Survey"] = relationship("Survey", back_populates="detections")
    job: Mapped["ProcessingJob"] = relationship("ProcessingJob", back_populates="detections")


class Report(Base):
    """Exported report files (JSON, CSV, GeoJSON) linked to a job."""

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType,
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    survey_id: Mapped[uuid.UUID] = mapped_column(
        UuidType,
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UuidType,
        ForeignKey("processing_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    format: Mapped[str] = mapped_column(String(16), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    detection_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()"),
    )

    __table_args__ = (
        CheckConstraint(
            "format IN ('json', 'csv', 'geojson')",
            name="ck_reports_format",
        ),
        Index("idx_reports_survey", "survey_id"),
        Index("idx_reports_job", "job_id"),
    )

    # Relationships
    survey: Mapped["Survey"] = relationship("Survey", back_populates="reports")
    job: Mapped["ProcessingJob"] = relationship("ProcessingJob", back_populates="reports")


class ModelRegistry(Base):
    """Tracks trained model versions."""

    __tablename__ = "model_registry"

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType,
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    model_name: Mapped[str] = mapped_column(String(256), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    task: Mapped[str] = mapped_column(String(32), nullable=False)
    architecture: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    framework: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    training_dataset: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dataset_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, default="MISSING_WEIGHTS")
    supported_classes: Mapped[Optional[List[str]]] = mapped_column(JsonType, nullable=True)
    metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JsonType, nullable=True)
    map50: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    map50_95: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dice_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    inference_latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    training_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JsonType, nullable=True)
    trained_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    registered_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()"),
    )

    __table_args__ = (
        CheckConstraint(
            "task IN ('detection', 'segmentation', 'edge_detection', 'classification')",
            name="ck_model_registry_task",
        ),
        UniqueConstraint("model_name", "version", "task", name="uq_model_version"),
        Index("idx_model_registry_task_active", "task", "is_active"),
    )


class LiveSonarSessionRecord(Base):
    """Database entity representing a continuous live sonar streaming session."""

    __tablename__ = "live_sonar_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="replay")
    source_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CONNECTING")
    preprocessing_profile: Mapped[str] = mapped_column(String(32), nullable=False, default="REALTIME")
    target_fps: Mapped[float] = mapped_column(Float, nullable=False, default=15.0)
    inference_fps: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)
    frames_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    frames_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    frames_dropped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_detections: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confirmed_targets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()"),
    )

    # Relationships
    tracks: Mapped[List["LiveTrackRecord"]] = relationship(
        "LiveTrackRecord", back_populates="session", cascade="all, delete-orphan"
    )
    events: Mapped[List["LiveDetectionEventRecord"]] = relationship(
        "LiveDetectionEventRecord", back_populates="session", cascade="all, delete-orphan"
    )
    evidence: Mapped[List["LiveEvidenceRecord"]] = relationship(
        "LiveEvidenceRecord", back_populates="session", cascade="all, delete-orphan"
    )


class LiveTrackRecord(Base):
    """Database entity representing a temporally confirmed target track."""

    __tablename__ = "live_sonar_tracks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("live_sonar_sessions.id", ondelete="CASCADE"), nullable=False
    )
    track_id: Mapped[int] = mapped_column(Integer, nullable=False)
    class_name: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="TENTATIVE")
    frames_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_seen_utc: Mapped[datetime] = mapped_column(nullable=False)
    last_seen_utc: Mapped[datetime] = mapped_column(nullable=False)
    bbox_x: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_y: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_w: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_h: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    depth_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    acoustic_shadow: Mapped[str] = mapped_column(String(32), nullable=False, default="unavailable")
    trajectory: Mapped[Optional[List[Any]]] = mapped_column(JsonType, nullable=True)

    session: Mapped["LiveSonarSessionRecord"] = relationship("LiveSonarSessionRecord", back_populates="tracks")


class LiveDetectionEventRecord(Base):
    """Individual live frame detection event."""

    __tablename__ = "live_detection_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("live_sonar_sessions.id", ondelete="CASCADE"), nullable=False
    )
    frame_id: Mapped[str] = mapped_column(String(64), nullable=False)
    track_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timestamp_utc: Mapped[datetime] = mapped_column(nullable=False)
    class_name: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_x: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_y: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_w: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_h: Mapped[int] = mapped_column(Integer, nullable=False)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    acoustic_shadow: Mapped[str] = mapped_column(String(32), nullable=False, default="unavailable")
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    processing_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, default="1.0.0")

    session: Mapped["LiveSonarSessionRecord"] = relationship("LiveSonarSessionRecord", back_populates="events")


class LiveEvidenceRecord(Base):
    """Forensic evidence snapshot captured for a confirmed track."""

    __tablename__ = "live_sonar_evidence"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("live_sonar_sessions.id", ondelete="CASCADE"), nullable=False
    )
    track_id: Mapped[int] = mapped_column(Integer, nullable=False)
    frame_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    raw_crop_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    enhanced_crop_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    annotated_crop_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JsonType, nullable=True)

    session: Mapped["LiveSonarSessionRecord"] = relationship("LiveSonarSessionRecord", back_populates="evidence")


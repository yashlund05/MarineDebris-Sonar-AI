"""Initial database schema matching DB_SCHEMA.md frozen v1.0.0.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-31 23:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. surveys table
    op.create_table(
        "surveys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_filename", sa.String(512), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("file_type", sa.String(16), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="uploaded"),
        sa.Column("channel", sa.String(16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.CheckConstraint("file_type IN ('xtf', 'jsf', 'png', 'tiff')", name="ck_surveys_file_type"),
        sa.CheckConstraint(
            "status IN ('uploaded', 'queued', 'preprocessing', 'inferring', "
            "'postprocessing', 'georeferencing', 'reporting', 'complete', 'failed')",
            name="ck_surveys_status",
        ),
        sa.CheckConstraint("channel IS NULL OR channel IN ('port', 'starboard', 'both', 'unknown')", name="ck_surveys_channel"),
    )
    op.create_index("idx_surveys_status", "surveys", ["status"])
    op.create_index("idx_surveys_created_at", "surveys", [sa.text("created_at DESC")])

    # 2. sonar_metadata table
    op.create_table(
        "sonar_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("frequency_hz", sa.Float(), nullable=True),
        sa.Column("samples_per_ping", sa.Integer(), nullable=True),
        sa.Column("total_pings", sa.Integer(), nullable=True),
        sa.Column("range_resolution_m", sa.Float(), nullable=True),
        sa.Column("along_track_resolution_m", sa.Float(), nullable=True),
        sa.Column("min_latitude", sa.Float(), nullable=True),
        sa.Column("max_latitude", sa.Float(), nullable=True),
        sa.Column("min_longitude", sa.Float(), nullable=True),
        sa.Column("max_longitude", sa.Float(), nullable=True),
        sa.Column("survey_start_time", sa.Float(), nullable=True),
        sa.Column("survey_end_time", sa.Float(), nullable=True),
        sa.Column("sonar_system", sa.String(128), nullable=True),
        sa.Column("motion_quality_score", sa.Float(), nullable=True),
        sa.Column("dropout_pct", sa.Float(), nullable=True),
        sa.Column("has_attitude_data", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("raw_header", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.UniqueConstraint("survey_id", name="uq_sonar_metadata_survey"),
    )

    # 3. processing_jobs table
    op.create_table(
        "processing_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("celery_task_id", sa.String(256), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("progress_pct", sa.SmallInteger(), nullable=True, server_default="0"),
        sa.Column("current_stage", sa.String(128), nullable=True),
        sa.Column("preprocessing_version", sa.String(64), nullable=True),
        sa.Column("detection_model", sa.String(256), nullable=True),
        sa.Column("detection_model_version", sa.String(64), nullable=True),
        sa.Column("segmentation_model", sa.String(256), nullable=True),
        sa.Column("detection_conf_threshold", sa.Float(), nullable=False, server_default="0.35"),
        sa.Column("nms_iou_threshold", sa.Float(), nullable=False, server_default="0.45"),
        sa.Column("tile_size", sa.Integer(), nullable=False, server_default="640"),
        sa.Column("tile_overlap", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status IN ('pending', 'running', 'complete', 'failed', 'cancelled')", name="ck_processing_jobs_status"),
        sa.CheckConstraint("progress_pct BETWEEN 0 AND 100", name="ck_processing_jobs_progress_pct"),
    )
    op.create_index("idx_jobs_survey_id", "processing_jobs", ["survey_id"])
    op.create_index("idx_jobs_status", "processing_jobs", ["status"])
    op.create_index("idx_jobs_celery_task", "processing_jobs", ["celery_task_id"])

    # 4. detections table
    op.create_table(
        "detections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("detection_code", sa.String(32), nullable=False),
        sa.Column("class_name", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("confidence_calibrated", sa.Float(), nullable=True),
        sa.Column("bbox_x", sa.Integer(), nullable=False),
        sa.Column("bbox_y", sa.Integer(), nullable=False),
        sa.Column("bbox_w", sa.Integer(), nullable=False),
        sa.Column("bbox_h", sa.Integer(), nullable=False),
        sa.Column("mask_rle", sa.Text(), nullable=True),
        sa.Column("estimated_length_m", sa.Float(), nullable=True),
        sa.Column("estimated_width_m", sa.Float(), nullable=True),
        sa.Column("geotagging_available", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("ping_number", sa.Integer(), nullable=True),
        sa.Column("ping_timestamp", sa.Float(), nullable=True),
        sa.Column("is_filtered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("filtered_reason", sa.String(256), nullable=True),
        sa.Column("source_tile_path", sa.String(1024), nullable=True),
        sa.Column("extra_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "class_name IN ('derelict_fishing_gear', 'general_marine_debris', 'shipwreck', "
            "'pipe_or_cylinder', 'other_man_made_target', 'natural_feature')",
            name="ck_detections_class_name",
        ),
    )
    op.create_index("idx_detections_survey", "detections", ["survey_id"])
    op.create_index("idx_detections_job", "detections", ["job_id"])
    op.create_index("idx_detections_class", "detections", ["class_name"])
    op.create_index("idx_detections_confidence", "detections", [sa.text("confidence DESC")])
    op.create_index("idx_detections_latlon", "detections", ["latitude", "longitude"])
    op.create_index("idx_detections_filtered", "detections", ["is_filtered"])

    # 5. reports table
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("format", sa.String(16), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("detection_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("format IN ('json', 'csv', 'geojson')", name="ck_reports_format"),
    )
    op.create_index("idx_reports_survey", "reports", ["survey_id"])
    op.create_index("idx_reports_job", "reports", ["job_id"])

    # 6. model_registry table
    op.create_table(
        "model_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("model_name", sa.String(256), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("task", sa.String(32), nullable=False),
        sa.Column("architecture", sa.String(128), nullable=True),
        sa.Column("training_dataset", sa.Text(), nullable=True),
        sa.Column("map50", sa.Float(), nullable=True),
        sa.Column("map50_95", sa.Float(), nullable=True),
        sa.Column("dice_score", sa.Float(), nullable=True),
        sa.Column("inference_latency_ms", sa.Float(), nullable=True),
        sa.Column("weight_path", sa.String(1024), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("training_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("task IN ('detection', 'segmentation', 'edge_detection')", name="ck_model_registry_task"),
        sa.UniqueConstraint("model_name", "version", "task", name="uq_model_version"),
    )
    op.create_index("idx_model_registry_task_active", "model_registry", ["task", "is_active"])


def downgrade() -> None:
    op.drop_table("model_registry")
    op.drop_table("reports")
    op.drop_table("detections")
    op.drop_table("processing_jobs")
    op.drop_table("sonar_metadata")
    op.drop_table("surveys")

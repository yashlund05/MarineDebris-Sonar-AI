"""Add Live Sonar subsystem tables: live_sonar_sessions, live_sonar_tracks, live_detection_events, live_sonar_evidence.

Revision ID: 0003_live_sonar_subsystem
Revises: 0002_ml_segmentation_classification
Create Date: 2026-09-19 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_live_sonar_subsystem"
down_revision: Union[str, None] = "0002_ml_segmentation_classification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    json_type = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

    # 1. live_sonar_sessions
    op.create_table(
        "live_sonar_sessions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False, server_default=""),
        sa.Column("source_type", sa.String(32), nullable=False, server_default="replay"),
        sa.Column("source_uri", sa.String(1024), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="CONNECTING"),
        sa.Column("preprocessing_profile", sa.String(32), nullable=False, server_default="REALTIME"),
        sa.Column("target_fps", sa.Float(), nullable=False, server_default="15.0"),
        sa.Column("inference_fps", sa.Float(), nullable=False, server_default="10.0"),
        sa.Column("frames_received", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("frames_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("frames_dropped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_detections", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confirmed_targets", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_live_sessions_status", "live_sonar_sessions", ["status"])

    # 2. live_sonar_tracks
    op.create_table(
        "live_sonar_tracks",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("live_sonar_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("class_name", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="TENTATIVE"),
        sa.Column("frames_seen", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_seen_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("bbox_x", sa.Integer(), nullable=False),
        sa.Column("bbox_y", sa.Integer(), nullable=False),
        sa.Column("bbox_w", sa.Integer(), nullable=False),
        sa.Column("bbox_h", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("depth_m", sa.Float(), nullable=True),
        sa.Column("acoustic_shadow", sa.String(32), nullable=False, server_default="unavailable"),
        sa.Column("trajectory", json_type, nullable=True),
    )
    op.create_index("idx_live_tracks_session", "live_sonar_tracks", ["session_id"])
    op.create_index("idx_live_tracks_status", "live_sonar_tracks", ["status"])

    # 3. live_detection_events
    op.create_table(
        "live_detection_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("live_sonar_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("frame_id", sa.String(64), nullable=False),
        sa.Column("track_id", sa.Integer(), nullable=True),
        sa.Column("timestamp_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("class_name", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("bbox_x", sa.Integer(), nullable=False),
        sa.Column("bbox_y", sa.Integer(), nullable=False),
        sa.Column("bbox_w", sa.Integer(), nullable=False),
        sa.Column("bbox_h", sa.Integer(), nullable=False),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("acoustic_shadow", sa.String(32), nullable=False, server_default="unavailable"),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("processing_latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("model_version", sa.String(64), nullable=False, server_default="1.0.0"),
    )
    op.create_index("idx_live_events_session", "live_detection_events", ["session_id"])
    op.create_index("idx_live_events_frame", "live_detection_events", ["frame_id"])

    # 4. live_sonar_evidence
    op.create_table(
        "live_sonar_evidence",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("live_sonar_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("frame_id", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("raw_crop_path", sa.String(1024), nullable=True),
        sa.Column("enhanced_crop_path", sa.String(1024), nullable=True),
        sa.Column("annotated_crop_path", sa.String(1024), nullable=True),
        sa.Column("metadata_json", json_type, nullable=True),
    )
    op.create_index("idx_live_evidence_session_track", "live_sonar_evidence", ["session_id", "track_id"])


def downgrade() -> None:
    op.drop_table("live_sonar_evidence")
    op.drop_table("live_detection_events")
    op.drop_table("live_sonar_tracks")
    op.drop_table("live_sonar_sessions")

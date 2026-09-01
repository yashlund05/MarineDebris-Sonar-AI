"""Add segmentation and classification tracking columns to detections and model_registry.

Revision ID: 0002_ml_segmentation_classification
Revises: 0001_initial_schema
Create Date: 2026-09-01 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_ml_segmentation_classification"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add segmentation and classification fields to detections table
    op.add_column(
        "detections",
        sa.Column("segmentation_status", sa.String(32), nullable=True, server_default="unavailable"),
    )
    op.add_column("detections", sa.Column("segmentation_confidence", sa.Float(), nullable=True))
    op.add_column("detections", sa.Column("mask_area", sa.Float(), nullable=True))
    op.add_column(
        "detections",
        sa.Column("mask_geometry", sa.JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True),
    )
    op.add_column(
        "detections",
        sa.Column("classification_status", sa.String(32), nullable=True, server_default="unavailable"),
    )
    op.add_column("detections", sa.Column("classifier_name", sa.String(128), nullable=True))
    op.add_column("detections", sa.Column("classifier_class", sa.String(64), nullable=True))
    op.add_column("detections", sa.Column("classifier_confidence", sa.Float(), nullable=True))
    op.add_column("detections", sa.Column("classification_agreement", sa.Boolean(), nullable=True))

    # 2. Add metadata and classification support to model_registry table
    op.add_column("model_registry", sa.Column("framework", sa.String(128), nullable=True))
    op.add_column("model_registry", sa.Column("dataset_version", sa.String(64), nullable=True))
    op.add_column(
        "model_registry",
        sa.Column("status", sa.String(32), nullable=True, server_default="MISSING_WEIGHTS"),
    )
    op.add_column(
        "model_registry",
        sa.Column("supported_classes", sa.JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True),
    )
    op.add_column(
        "model_registry",
        sa.Column("metrics", sa.JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("model_registry", "metrics")
    op.drop_column("model_registry", "supported_classes")
    op.drop_column("model_registry", "status")
    op.drop_column("model_registry", "dataset_version")
    op.drop_column("model_registry", "framework")

    op.drop_column("detections", "classification_agreement")
    op.drop_column("detections", "classifier_confidence")
    op.drop_column("detections", "classifier_class")
    op.drop_column("detections", "classifier_name")
    op.drop_column("detections", "classification_status")
    op.drop_column("detections", "mask_geometry")
    op.drop_column("detections", "mask_area")
    op.drop_column("detections", "segmentation_confidence")
    op.drop_column("detections", "segmentation_status")

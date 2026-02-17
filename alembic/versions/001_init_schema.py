"""init

Revision ID: 001_init
Revises:
Create Date: 2026-02-17

Initial schema per docs/plan.md: states, categories, monitored_urls, pdf_versions,
change_log, monitoring_cycles, cycle_url_results, schedule_config, sessions.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # states
    op.create_table(
        "states",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("abbreviation", sa.String(length=16), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_states_abbreviation", "states", ["abbreviation"], unique=True)
    op.create_index("ix_states_is_active", "states", ["is_active"], unique=False)

    # categories
    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_category_id", sa.BigInteger(), nullable=True),
        sa.Column("state_id", sa.BigInteger(), nullable=False),
        sa.Column("full_path", sa.String(length=1024), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["parent_category_id"],
            ["categories.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["state_id"],
            ["states.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_categories_state_id", "categories", ["state_id"], unique=False)
    op.create_index(
        "ix_categories_parent_category_id",
        "categories",
        ["parent_category_id"],
        unique=False,
    )
    op.create_index("ix_categories_full_path", "categories", ["full_path"], unique=False)

    # monitored_urls
    op.create_table(
        "monitored_urls",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("form_number", sa.String(length=128), nullable=True),
        sa.Column("revision_date", sa.Date(), nullable=True),
        sa.Column("state_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_checked", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["state_id"],
            ["states.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitored_urls_state_id", "monitored_urls", ["state_id"], unique=False)
    op.create_index("ix_monitored_urls_category_id", "monitored_urls", ["category_id"], unique=False)
    op.create_index("ix_monitored_urls_status", "monitored_urls", ["status"], unique=False)
    op.create_index("ix_monitored_urls_is_enabled", "monitored_urls", ["is_enabled"], unique=False)
    op.create_index(
        "ix_monitored_urls_last_checked",
        "monitored_urls",
        ["last_checked"],
        unique=False,
    )

    # pdf_versions
    op.create_table(
        "pdf_versions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("url_id", sa.BigInteger(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("pdf_hash", sa.String(length=64), nullable=False),
        sa.Column("text_hash", sa.String(length=64), nullable=True),
        sa.Column("normalized_hash", sa.String(length=64), nullable=True),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("text_content", sa.Text(), nullable=True),
        sa.Column("s3_raw_key", sa.String(length=512), nullable=True),
        sa.Column("s3_normalized_key", sa.String(length=512), nullable=True),
        sa.Column("s3_extracted_key", sa.String(length=512), nullable=True),
        sa.Column("s3_text_key", sa.String(length=512), nullable=True),
        sa.Column("opensearch_document_id", sa.String(length=128), nullable=True),
        sa.Column("opensearch_indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opensearch_index_status", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["url_id"],
            ["monitored_urls.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url_id", "version_number", name="uq_pdf_versions_url_version"),
    )
    op.create_index("ix_pdf_versions_url_id", "pdf_versions", ["url_id"], unique=False)
    op.create_index("ix_pdf_versions_created_at", "pdf_versions", ["created_at"], unique=False)
    op.create_index(
        "ix_pdf_versions_opensearch_document_id",
        "pdf_versions",
        ["opensearch_document_id"],
        unique=False,
    )

    # change_log
    op.create_table(
        "change_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("url_id", sa.BigInteger(), nullable=False),
        sa.Column("version_id", sa.BigInteger(), nullable=False),
        sa.Column("change_type", sa.String(length=64), nullable=False),
        sa.Column("classification", sa.String(length=128), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reviewed_by", sa.String(length=255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["url_id"],
            ["monitored_urls.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["version_id"],
            ["pdf_versions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_change_log_url_id", "change_log", ["url_id"], unique=False)
    op.create_index("ix_change_log_version_id", "change_log", ["version_id"], unique=False)
    op.create_index("ix_change_log_status", "change_log", ["status"], unique=False)
    op.create_index("ix_change_log_created_at", "change_log", ["created_at"], unique=False)

    # monitoring_cycles
    op.create_table(
        "monitoring_cycles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_urls", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "changes_detected",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("errors", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_monitoring_cycles_status",
        "monitoring_cycles",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_monitoring_cycles_started_at",
        "monitoring_cycles",
        ["started_at"],
        unique=False,
    )

    # cycle_url_results
    op.create_table(
        "cycle_url_results",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("cycle_id", sa.BigInteger(), nullable=False),
        sa.Column("url_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "change_detected",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["cycle_id"],
            ["monitoring_cycles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["url_id"],
            ["monitored_urls.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cycle_url_results_cycle_id",
        "cycle_url_results",
        ["cycle_id"],
        unique=False,
    )
    op.create_index(
        "ix_cycle_url_results_url_id",
        "cycle_url_results",
        ["url_id"],
        unique=False,
    )

    # schedule_config
    op.create_table(
        "schedule_config",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("cron_expression", sa.String(length=128), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # sessions (BFF)
    op.create_table(
        "sessions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sessions_token", "sessions", ["token"], unique=True)
    op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sessions_expires_at", table_name="sessions")
    op.drop_index("ix_sessions_token", table_name="sessions", unique=True)
    op.drop_table("sessions")

    op.drop_table("schedule_config")

    op.drop_index("ix_cycle_url_results_url_id", table_name="cycle_url_results")
    op.drop_index("ix_cycle_url_results_cycle_id", table_name="cycle_url_results")
    op.drop_table("cycle_url_results")

    op.drop_index("ix_monitoring_cycles_started_at", table_name="monitoring_cycles")
    op.drop_index("ix_monitoring_cycles_status", table_name="monitoring_cycles")
    op.drop_table("monitoring_cycles")

    op.drop_index("ix_change_log_created_at", table_name="change_log")
    op.drop_index("ix_change_log_status", table_name="change_log")
    op.drop_index("ix_change_log_version_id", table_name="change_log")
    op.drop_index("ix_change_log_url_id", table_name="change_log")
    op.drop_table("change_log")

    op.drop_index("ix_pdf_versions_opensearch_document_id", table_name="pdf_versions")
    op.drop_index("ix_pdf_versions_created_at", table_name="pdf_versions")
    op.drop_index("ix_pdf_versions_url_id", table_name="pdf_versions")
    op.drop_table("pdf_versions")

    op.drop_index("ix_monitored_urls_last_checked", table_name="monitored_urls")
    op.drop_index("ix_monitored_urls_is_enabled", table_name="monitored_urls")
    op.drop_index("ix_monitored_urls_status", table_name="monitored_urls")
    op.drop_index("ix_monitored_urls_category_id", table_name="monitored_urls")
    op.drop_index("ix_monitored_urls_state_id", table_name="monitored_urls")
    op.drop_table("monitored_urls")

    op.drop_index("ix_categories_full_path", table_name="categories")
    op.drop_index("ix_categories_parent_category_id", table_name="categories")
    op.drop_index("ix_categories_state_id", table_name="categories")
    op.drop_table("categories")

    op.drop_index("ix_states_is_active", table_name="states")
    op.drop_index("ix_states_abbreviation", table_name="states", unique=True)
    op.drop_table("states")

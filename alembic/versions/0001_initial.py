"""Initial schema.

Revision ID: 0001
Revises: None
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("username", sa.String(255)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_users_external_id", "users", ["external_id"])
    op.create_table(
        "wines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("brand", sa.String(255)),
        sa.Column("country", sa.String(120)),
        sa.Column("region", sa.String(255)),
        sa.Column("color", sa.String(32)),
        sa.Column("sugar_type", sa.String(32)),
        sa.Column("grape", sa.String(255)),
        sa.Column("volume", sa.Float()),
        sa.Column("description", sa.Text()),
        sa.Column("image_url", sa.Text()),
        sa.Column("product_url", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_wines_external_id", "wines", ["external_id"])
    op.create_index("ix_wines_color", "wines", ["color"])
    op.create_index("ix_wines_sugar_type", "wines", ["sugar_type"])
    op.create_table(
        "wine_offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "wine_id", sa.Integer(), sa.ForeignKey("wines.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("source", sa.String(80), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("old_price", sa.Numeric(12, 2)),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("external_rating", sa.Float()),
        sa.Column("reviews_count", sa.Integer(), nullable=False),
        sa.Column("product_url", sa.Text()),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("wine_id", "source", name="uq_offer_wine_source"),
    )
    op.create_index("ix_wine_offers_wine_id", "wine_offers", ["wine_id"])
    op.create_index("ix_wine_offers_source", "wine_offers", ["source"])
    op.create_table(
        "user_likes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "wine_id", sa.Integer(), sa.ForeignKey("wines.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("user_id", "wine_id", name="uq_user_like"),
    )
    op.create_table(
        "recommendation_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("raw_query", sa.Text(), nullable=False),
        sa.Column("parsed_params", sa.JSON(), nullable=False),
        sa.Column("recommended_wine_ids", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_recommendation_events_user_id", "recommendation_events", ["user_id"])


def downgrade() -> None:
    op.drop_table("recommendation_events")
    op.drop_table("user_likes")
    op.drop_table("wine_offers")
    op.drop_table("wines")
    op.drop_table("users")

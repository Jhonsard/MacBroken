"""Initial schema — users, mac_history, chat_logs.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Type ENUM natif PostgreSQL pour le statut de spoofing
    # ------------------------------------------------------------------
    mac_status = postgresql.ENUM(
        "PENDING", "SUCCESS", "FAILED", "CANCELLED",
        name="mac_spoof_status", create_type=False,
    )
    mac_status.create(op.get_bind(), checkfirst=True)

    # ------------------------------------------------------------------
    # Table users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_users_created_at", "users", ["created_at"], unique=False)

    # ------------------------------------------------------------------
    # Table mac_history
    # ------------------------------------------------------------------
    op.create_table(
        "mac_history",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("interface_name", sa.String(length=32), nullable=False),
        sa.Column("original_mac", sa.String(length=17), nullable=False),
        sa.Column("spoofed_mac", sa.String(length=17), nullable=False),
        sa.Column("status", mac_status, nullable=False, server_default="PENDING"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_mac_history_user_id", ondelete="CASCADE",
        ),
    )
    op.create_index("ix_mac_history_user_id", "mac_history", ["user_id"], unique=False)
    op.create_index("ix_mac_history_status", "mac_history", ["status"], unique=False)
    op.create_index("ix_mac_history_timestamp", "mac_history", ["timestamp"], unique=False)

    # ------------------------------------------------------------------
    # Table chat_logs
    # ------------------------------------------------------------------
    op.create_table(
        "chat_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_chat_logs_user_id", ondelete="CASCADE",
        ),
    )
    op.create_index("ix_chat_logs_user_id", "chat_logs", ["user_id"], unique=False)
    op.create_index("ix_chat_logs_timestamp", "chat_logs", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_chat_logs_timestamp", table_name="chat_logs")
    op.drop_index("ix_chat_logs_user_id", table_name="chat_logs")
    op.drop_table("chat_logs")

    op.drop_index("ix_mac_history_timestamp", table_name="mac_history")
    op.drop_index("ix_mac_history_status", table_name="mac_history")
    op.drop_index("ix_mac_history_user_id", table_name="mac_history")
    op.drop_table("mac_history")

    op.drop_index("ix_users_created_at", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")

    # Drop ENUM
    postgresql.ENUM(name="mac_spoof_status").drop(op.get_bind(), checkfirst=True)
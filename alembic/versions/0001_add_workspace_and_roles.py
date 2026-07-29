"""add workspace_id and workspace member roles

Revision ID: 0001_add_workspace_and_roles
Revises: None
Create Date: 2026-07-29 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_add_workspace_and_roles"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add users.role if missing
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("role", sa.String(length=20), nullable=False, server_default="MEMBER"))
        # remove server default to match models
        batch_op.alter_column("role", server_default=None)

    # Add workspace_id to projects
    with op.batch_alter_table("projects", schema=None) as batch_op:
        batch_op.add_column(sa.Column("workspace_id", sa.String(length=36), nullable=True))

    # Add role to workspace_members
    with op.batch_alter_table("workspace_members", schema=None) as batch_op:
        batch_op.add_column(sa.Column("role", sa.String(length=20), nullable=False, server_default="EDITOR"))
        batch_op.alter_column("role", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("workspace_members", schema=None) as batch_op:
        batch_op.drop_column("role")

    with op.batch_alter_table("projects", schema=None) as batch_op:
        batch_op.drop_column("workspace_id")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("role")

from alembic import op
import sqlalchemy as sa
import uuid

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column("external_user_id", sa.String(128), unique=True, index=True, nullable=False),
        sa.Column("api_key_hash", sa.String(64), index=True, nullable=False, server_default=""),
        sa.Column("balance_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "generations",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, index=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("input_image_url", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(32), nullable=False, server_default="fal"),
        sa.Column("provider_request_id", sa.String(128), nullable=True, index=True),
        sa.Column("cost_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result_url", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("callback_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "outbox_webhooks",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column("target_url", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

def downgrade():
    op.drop_table("outbox_webhooks")
    op.drop_table("generations")
    op.drop_table("users")

"""add conversation topics

Revision ID: 20260107_1131
Revises:
Create Date: 2026-01-07 11:31:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260107_1131'
down_revision = None  # Update this if there's a previous migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create conversation_topics table
    op.create_table('conversation_topics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('topic_title', sa.String(length=255), nullable=True),
        sa.Column('topic_summary', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add topic_id column to conversation_messages
    op.add_column('conversation_messages',
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'conversation_messages_topic_id_fkey',
        'conversation_messages', 'conversation_topics',
        ['topic_id'], ['id']
    )

    # Create indexes for performance
    op.create_index(
        'ix_conversation_topics_project_id_active',
        'conversation_topics',
        ['project_id', 'is_active']
    )
    op.create_index(
        'ix_conversation_messages_topic_id',
        'conversation_messages',
        ['topic_id']
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_conversation_messages_topic_id', table_name='conversation_messages')
    op.drop_index('ix_conversation_topics_project_id_active', table_name='conversation_topics')

    # Drop foreign key and column
    op.drop_constraint('conversation_messages_topic_id_fkey', 'conversation_messages', type_='foreignkey')
    op.drop_column('conversation_messages', 'topic_id')

    # Drop table
    op.drop_table('conversation_topics')

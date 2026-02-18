"""Initial migration

Revision ID: 20240218_initial
Revises: 
Create Date: 2024-02-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20240218_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tenants
    op.create_table('tenants',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('plan', sa.String(length=50), server_default='free', nullable=False),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('usage_limits', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('current_usage', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenants_slug'), 'tenants', ['slug'], unique=True)
    op.create_index(op.f('ix_tenants_id'), 'tenants', ['id'], unique=False)

    # 2. Memberships
    op.create_table('memberships',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='viewer', nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_memberships_user_tenant', 'memberships', ['user_id', 'tenant_id'], unique=False)
    op.create_index(op.f('ix_memberships_tenant_id'), 'memberships', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_memberships_user_id'), 'memberships', ['user_id'], unique=False)

    # 3. Lead Lists
    op.create_table('lead_lists',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('list_type', sa.String(length=20), server_default='static', nullable=False),
        sa.Column('filters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lead_lists_tenant_type', 'lead_lists', ['tenant_id', 'list_type'], unique=False)
    op.create_index(op.f('ix_lead_lists_tenant_id'), 'lead_lists', ['tenant_id'], unique=False)

    # 4. Leads
    op.create_table('leads',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('timezone', sa.String(length=50), server_default='UTC', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='new', nullable=False),
        sa.Column('custom_fields', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_leads_tenant_email', 'leads', ['tenant_id', 'email'], unique=False)
    op.create_index('ix_leads_tenant_phone', 'leads', ['tenant_id', 'phone'], unique=False)
    op.create_index('ix_leads_tenant_status', 'leads', ['tenant_id', 'status'], unique=False)
    op.create_index(op.f('ix_leads_email'), 'leads', ['email'], unique=False)
    op.create_index(op.f('ix_leads_phone'), 'leads', ['phone'], unique=False)
    op.create_index(op.f('ix_leads_tenant_id'), 'leads', ['tenant_id'], unique=False)

    # 5. Lead List Items
    op.create_table('lead_list_items',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('lead_list_id', sa.UUID(), nullable=False),
        sa.Column('lead_id', sa.UUID(), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lead_list_id'], ['lead_lists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lead_list_items_list_lead', 'lead_list_items', ['lead_list_id', 'lead_id'], unique=True)
    op.create_index(op.f('ix_lead_list_items_lead_id'), 'lead_list_items', ['lead_id'], unique=False)
    op.create_index(op.f('ix_lead_list_items_lead_list_id'), 'lead_list_items', ['lead_list_id'], unique=False)

    # 6. Campaigns
    op.create_table('campaigns',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('channel', sa.String(length=20), nullable=False),
        sa.Column('lead_list_id', sa.UUID(), nullable=True),
        sa.Column('start_datetime', sa.DateTime(), nullable=False),
        sa.Column('timezone', sa.String(length=50), server_default='UTC', nullable=False),
        sa.Column('retry_strategy', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='draft', nullable=False),
        sa.Column('message_content', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('total_targets', sa.Integer(), server_default='0', nullable=False),
        sa.Column('completed_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('failed_count', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['lead_list_id'], ['lead_lists.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_campaigns_tenant_channel', 'campaigns', ['tenant_id', 'channel'], unique=False)
    op.create_index('ix_campaigns_tenant_status', 'campaigns', ['tenant_id', 'status'], unique=False)
    op.create_index(op.f('ix_campaigns_tenant_id'), 'campaigns', ['tenant_id'], unique=False)

    # 7. Campaign Schedule Rules
    op.create_table('campaign_schedule_rules',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('campaign_id', sa.UUID(), nullable=False),
        sa.Column('start_hour', sa.Integer(), server_default='9', nullable=False),
        sa.Column('end_hour', sa.Integer(), server_default='17', nullable=False),
        sa.Column('days_allowed', sa.ARRAY(sa.Integer()), server_default='{0,1,2,3,4}', nullable=False),
        sa.Column('blackout_dates', sa.ARRAY(sa.String()), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_campaign_schedule_rules_campaign_id'), 'campaign_schedule_rules', ['campaign_id'], unique=False)

    # 8. Campaign Targets
    op.create_table('campaign_targets',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('campaign_id', sa.UUID(), nullable=False),
        sa.Column('lead_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('attempt_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('next_attempt_at', sa.DateTime(), nullable=True),
        sa.Column('last_attempt_at', sa.DateTime(), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_campaign_targets_campaign_lead', 'campaign_targets', ['campaign_id', 'lead_id'], unique=True)
    op.create_index('ix_campaign_targets_campaign_status', 'campaign_targets', ['campaign_id', 'status'], unique=False)
    op.create_index('ix_campaign_targets_next_attempt', 'campaign_targets', ['next_attempt_at'], unique=False)
    op.create_index(op.f('ix_campaign_targets_campaign_id'), 'campaign_targets', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_campaign_targets_lead_id'), 'campaign_targets', ['lead_id'], unique=False)

    # 9. Automations
    op.create_table('automations',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('trigger_type', sa.String(length=50), nullable=False),
        sa.Column('trigger_config', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_automations_tenant_enabled', 'automations', ['tenant_id', 'enabled'], unique=False)
    op.create_index('ix_automations_trigger_type', 'automations', ['trigger_type'], unique=False)
    op.create_index(op.f('ix_automations_tenant_id'), 'automations', ['tenant_id'], unique=False)

    # 10. Automation Conditions
    op.create_table('automation_conditions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('automation_id', sa.UUID(), nullable=False),
        sa.Column('condition_type', sa.String(length=50), nullable=False),
        sa.Column('condition_config', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('order', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['automation_id'], ['automations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_automation_conditions_automation_id'), 'automation_conditions', ['automation_id'], unique=False)

    # 11. Automation Actions
    op.create_table('automation_actions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('automation_id', sa.UUID(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('action_config', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('delay_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['automation_id'], ['automations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_automation_actions_automation_id'), 'automation_actions', ['automation_id'], unique=False)

    # 12. Conversations
    op.create_table('conversations',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('lead_id', sa.UUID(), nullable=False),
        sa.Column('channel', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='open', nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversations_tenant_lead', 'conversations', ['tenant_id', 'lead_id'], unique=False)
    op.create_index('ix_conversations_tenant_status', 'conversations', ['tenant_id', 'status'], unique=False)
    op.create_index(op.f('ix_conversations_external_id'), 'conversations', ['external_id'], unique=False)
    op.create_index(op.f('ix_conversations_lead_id'), 'conversations', ['lead_id'], unique=False)
    op.create_index(op.f('ix_conversations_tenant_id'), 'conversations', ['tenant_id'], unique=False)

    # 13. Messages
    op.create_table('messages',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('sender_type', sa.String(length=20), nullable=False),
        sa.Column('sender_id', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=20), server_default='text', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='sent', nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_conversation_created', 'messages', ['conversation_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_messages_external_id'), 'messages', ['external_id'], unique=False)

    # 14. SEO Projects
    op.create_table('seo_projects',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('target_country', sa.String(length=10), server_default='US', nullable=False),
        sa.Column('target_language', sa.String(length=10), server_default='en', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_seo_projects_tenant_status', 'seo_projects', ['tenant_id', 'status'], unique=False)
    op.create_index(op.f('ix_seo_projects_tenant_id'), 'seo_projects', ['tenant_id'], unique=False)

    # 15. SEO Keywords
    op.create_table('seo_keywords',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('keyword', sa.String(length=255), nullable=False),
        sa.Column('search_volume', sa.Integer(), server_default='0', nullable=False),
        sa.Column('difficulty', sa.Integer(), server_default='0', nullable=False),
        sa.Column('current_rank', sa.Integer(), nullable=True),
        sa.Column('target_url', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['seo_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_seo_keywords_project_keyword', 'seo_keywords', ['project_id', 'keyword'], unique=True)
    op.create_index(op.f('ix_seo_keywords_project_id'), 'seo_keywords', ['project_id'], unique=False)

    # 16. Keyword Rank History
    op.create_table('keyword_rank_history',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('keyword_id', sa.UUID(), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('url', sa.String(length=500), nullable=True),
        sa.Column('search_volume', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['keyword_id'], ['seo_keywords.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_keyword_rank_history_keyword_created', 'keyword_rank_history', ['keyword_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_keyword_rank_history_keyword_id'), 'keyword_rank_history', ['keyword_id'], unique=False)

    # 17. SEO Audits
    op.create_table('seo_audits',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('audit_type', sa.String(length=50), nullable=False),
        sa.Column('score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('results', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['seo_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_seo_audits_project_created', 'seo_audits', ['project_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_seo_audits_project_id'), 'seo_audits', ['project_id'], unique=False)

    # 18. SEO Issues
    op.create_table('seo_issues',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('audit_id', sa.UUID(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('issue_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('affected_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='open', nullable=False),
        sa.ForeignKeyConstraint(['audit_id'], ['seo_audits.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_seo_issues_audit_status', 'seo_issues', ['audit_id', 'status'], unique=False)
    op.create_index(op.f('ix_seo_issues_audit_id'), 'seo_issues', ['audit_id'], unique=False)

    # 19. Audit Logs
    op.create_table('audit_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.UUID(), nullable=True),
        sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'], unique=False)
    op.create_index('ix_audit_logs_tenant_created', 'audit_logs', ['tenant_id', 'created_at'], unique=False)
    op.create_index('ix_audit_logs_user_created', 'audit_logs', ['user_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_request_id'), 'audit_logs', ['request_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order of creation (dependencies first)
    op.drop_table('audit_logs')
    op.drop_table('seo_issues')
    op.drop_table('seo_audits')
    op.drop_table('keyword_rank_history')
    op.drop_table('seo_keywords')
    op.drop_table('seo_projects')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('automation_actions')
    op.drop_table('automation_conditions')
    op.drop_table('automations')
    op.drop_table('campaign_targets')
    op.drop_table('campaign_schedule_rules')
    op.drop_table('campaigns')
    op.drop_table('lead_list_items')
    op.drop_table('leads')
    op.drop_table('lead_lists')
    op.drop_table('memberships')
    op.drop_table('tenants')

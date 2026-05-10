"""add geom to lockers

Revision ID: 110a8aa3b842
Revises: 539ca13f220d
Create Date: 2026-05-08 15:05:57.112986

"""
from collections.abc import Sequence

import geoalchemy2
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '110a8aa3b842'
down_revision: str | None = '539ca13f220d'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add nullable first so existing rows survive, backfill from lat/lng, then enforce NOT NULL.
    op.add_column(
        'lockers',
        sa.Column(
            'geom',
            geoalchemy2.types.Geography(
                geometry_type='POINT',
                srid=4326,
                from_text='ST_GeogFromText',
                name='geography',
            ),
            nullable=True,
        ),
    )
    op.execute(
        "UPDATE lockers "
        "SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography"
    )
    op.alter_column('lockers', 'geom', nullable=False)
    # GIST index auto-created by GeoAlchemy2 when the geography column is added.


def downgrade() -> None:
    op.drop_index('idx_lockers_geom', table_name='lockers', postgresql_using='gist')
    op.drop_column('lockers', 'geom')

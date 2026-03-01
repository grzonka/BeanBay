"""grinder_ring_sizes_display_format

Revision ID: 8d6331efcb5c
Revises: 9052fc4244a4
Create Date: 2026-02-28 11:13:31.322629

"""

import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


# revision identifiers, used by Alembic.
revision: str = "8d6331efcb5c"
down_revision: Union[str, Sequence[str], None] = "9052fc4244a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_column_names(inspector, table_name):
    """Return set of column names for a table, or empty set if table doesn't exist."""
    tables = inspector.get_table_names()
    if table_name not in tables:
        return set()
    return {col["name"] for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    """Add display_format + ring_sizes_json, populate from legacy data, drop legacy columns."""
    conn = op.get_bind()
    inspector = inspect(conn)
    grinders_cols = _get_column_names(inspector, "grinders")

    # 1. Add new columns if they don't already exist
    if "display_format" not in grinders_cols:
        with op.batch_alter_table("grinders", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column("display_format", sa.String(), nullable=False, server_default="decimal")
            )
        op.execute(text("UPDATE grinders SET display_format = 'decimal' WHERE display_format IS NULL"))

    if "ring_sizes_json" not in grinders_cols:
        with op.batch_alter_table("grinders", schema=None) as batch_op:
            batch_op.add_column(sa.Column("ring_sizes_json", sa.Text(), nullable=True))

    # 2. Populate ring_sizes_json from legacy columns (only if legacy columns still exist)
    # Re-inspect after potential column additions
    inspector = inspect(conn)
    grinders_cols = _get_column_names(inspector, "grinders")

    if "min_value" in grinders_cols and "max_value" in grinders_cols:
        # Read all existing grinders and compute ring_sizes from legacy data
        rows = conn.execute(
            text("SELECT id, dial_type, step_size, min_value, max_value FROM grinders")
        ).fetchall()
        for row in rows:
            grinder_id = row[0]
            dial_type = row[1]
            step_size = row[2]
            min_val = row[3]
            max_val = row[4]

            ring_min = min_val if min_val is not None else 0.0
            ring_max = max_val if max_val is not None else 50.0
            ring_step = step_size if dial_type == "stepped" else None
            ring_sizes = json.dumps([[ring_min, ring_max, ring_step]])

            conn.execute(
                text("UPDATE grinders SET ring_sizes_json = :rs WHERE id = :gid"),
                {"rs": ring_sizes, "gid": grinder_id},
            )

    # 3. Set display_format = "decimal" for any grinders that don't have it set
    conn.execute(
        text("UPDATE grinders SET display_format = 'decimal' WHERE display_format IS NULL")
    )

    # 4. Drop legacy columns
    legacy_cols = ["dial_type", "step_size", "min_value", "max_value"]
    cols_to_drop = [c for c in legacy_cols if c in grinders_cols]
    if cols_to_drop:
        with op.batch_alter_table("grinders", schema=None) as batch_op:
            for col in cols_to_drop:
                batch_op.drop_column(col)


def downgrade() -> None:
    """Re-add legacy columns, populate from ring_sizes_json, drop new columns."""
    conn = op.get_bind()
    inspector = inspect(conn)
    grinders_cols = _get_column_names(inspector, "grinders")

    # 1. Re-add legacy columns
    if "dial_type" not in grinders_cols:
        with op.batch_alter_table("grinders", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column("dial_type", sa.String(), nullable=False, server_default="stepless")
            )

    if "step_size" not in grinders_cols:
        with op.batch_alter_table("grinders", schema=None) as batch_op:
            batch_op.add_column(sa.Column("step_size", sa.Float(), nullable=True))

    if "min_value" not in grinders_cols:
        with op.batch_alter_table("grinders", schema=None) as batch_op:
            batch_op.add_column(sa.Column("min_value", sa.Float(), nullable=True))

    if "max_value" not in grinders_cols:
        with op.batch_alter_table("grinders", schema=None) as batch_op:
            batch_op.add_column(sa.Column("max_value", sa.Float(), nullable=True))

    # 2. Populate legacy columns from ring_sizes_json (if it exists)
    inspector = inspect(conn)
    grinders_cols = _get_column_names(inspector, "grinders")

    if "ring_sizes_json" in grinders_cols:
        rows = conn.execute(
            text("SELECT id, ring_sizes_json FROM grinders")
        ).fetchall()
        for row in rows:
            grinder_id = row[0]
            ring_sizes_json = row[1]
            if ring_sizes_json:
                rings = json.loads(ring_sizes_json)
                if rings and len(rings) > 0:
                    ring = rings[0]  # Use first ring for legacy columns
                    min_val = ring[0]
                    max_val = ring[1]
                    step = ring[2] if len(ring) > 2 else None
                    dial_type = "stepped" if step is not None else "stepless"

                    conn.execute(
                        text(
                            "UPDATE grinders SET dial_type = :dt, step_size = :ss, "
                            "min_value = :mi, max_value = :ma WHERE id = :gid"
                        ),
                        {
                            "dt": dial_type,
                            "ss": step,
                            "mi": min_val,
                            "ma": max_val,
                            "gid": grinder_id,
                        },
                    )

    # 3. Drop new columns
    new_cols = ["display_format", "ring_sizes_json"]
    cols_to_drop = [c for c in new_cols if c in grinders_cols]
    if cols_to_drop:
        with op.batch_alter_table("grinders", schema=None) as batch_op:
            for col in cols_to_drop:
                batch_op.drop_column(col)

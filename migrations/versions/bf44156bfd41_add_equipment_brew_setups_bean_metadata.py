"""add_equipment_brew_setups_bean_metadata

Revision ID: bf44156bfd41
Revises: c06d948aa2d7
Create Date: 2026-02-22 23:53:51.307306

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bf44156bfd41"
down_revision: Union[str, Sequence[str], None] = "c06d948aa2d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Deterministic UUIDs for seeded default data — must be stable across runs
DEFAULT_METHOD_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_SETUP_ID = "00000000-0000-0000-0000-000000000002"


def upgrade() -> None:
    """Upgrade schema: create equipment/setup tables, extend beans and measurements, seed defaults."""

    # Get list of existing tables to handle idempotency
    # (app lifespan runs Base.metadata.create_all() so tables may already exist)
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # ── Create new tables (brew_methods must come before brew_setups — FK dependency) ──

    if "brew_methods" not in existing_tables:
        op.create_table(
            "brew_methods",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )

    if "grinders" not in existing_tables:
        op.create_table(
            "grinders",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if "brewers" not in existing_tables:
        op.create_table(
            "brewers",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if "papers" not in existing_tables:
        op.create_table(
            "papers",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if "water_recipes" not in existing_tables:
        op.create_table(
            "water_recipes",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("recipe_details", sa.String(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if "brew_setups" not in existing_tables:
        op.create_table(
            "brew_setups",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("brew_method_id", sa.String(), nullable=False),
            sa.Column("grinder_id", sa.String(), nullable=True),
            sa.Column("brewer_id", sa.String(), nullable=True),
            sa.Column("paper_id", sa.String(), nullable=True),
            sa.Column("water_recipe_id", sa.String(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["brew_method_id"], ["brew_methods.id"]),
            sa.ForeignKeyConstraint(["brewer_id"], ["brewers.id"]),
            sa.ForeignKeyConstraint(["grinder_id"], ["grinders.id"]),
            sa.ForeignKeyConstraint(["paper_id"], ["papers.id"]),
            sa.ForeignKeyConstraint(["water_recipe_id"], ["water_recipes.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "bags" not in existing_tables:
        op.create_table(
            "bags",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("bean_id", sa.String(), nullable=False),
            sa.Column("purchase_date", sa.Date(), nullable=True),
            sa.Column("cost", sa.Float(), nullable=True),
            sa.Column("weight_grams", sa.Float(), nullable=True),
            sa.Column("notes", sa.String(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["bean_id"], ["beans.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_bags_bean_id", "bags", ["bean_id"], unique=False)

    # ── Add columns to beans (batch_alter_table required for SQLite) ──

    existing_bean_cols = {c["name"] for c in inspector.get_columns("beans")}
    with op.batch_alter_table("beans", schema=None) as batch_op:
        if "roast_date" not in existing_bean_cols:
            batch_op.add_column(sa.Column("roast_date", sa.Date(), nullable=True))
        if "process" not in existing_bean_cols:
            batch_op.add_column(sa.Column("process", sa.String(), nullable=True))
        if "variety" not in existing_bean_cols:
            batch_op.add_column(sa.Column("variety", sa.String(), nullable=True))

    # ── Add brew_setup_id column to measurements ──

    existing_meas_cols = {c["name"] for c in inspector.get_columns("measurements")}
    with op.batch_alter_table("measurements", schema=None) as batch_op:
        if "brew_setup_id" not in existing_meas_cols:
            batch_op.add_column(sa.Column("brew_setup_id", sa.String(), nullable=True))
            batch_op.create_index(
                batch_op.f("ix_measurements_brew_setup_id"),
                ["brew_setup_id"],
                unique=False,
            )
            batch_op.create_foreign_key(
                "fk_measurements_brew_setup_id", "brew_setups", ["brew_setup_id"], ["id"]
            )

    # ── Data migration: seed default Espresso method + setup, link existing measurements ──

    # Check if default brew method already exists (idempotent re-run safety)
    result = bind.execute(
        sa.text("SELECT COUNT(*) FROM brew_methods WHERE id = :id"),
        {"id": DEFAULT_METHOD_ID},
    )
    if result.scalar() == 0:
        op.execute(
            f"INSERT INTO brew_methods (id, name, created_at) "
            f"VALUES ('{DEFAULT_METHOD_ID}', 'Espresso', CURRENT_TIMESTAMP)"
        )

    result = bind.execute(
        sa.text("SELECT COUNT(*) FROM brew_setups WHERE id = :id"),
        {"id": DEFAULT_SETUP_ID},
    )
    if result.scalar() == 0:
        op.execute(
            f"INSERT INTO brew_setups (id, brew_method_id, created_at) "
            f"VALUES ('{DEFAULT_SETUP_ID}', '{DEFAULT_METHOD_ID}', CURRENT_TIMESTAMP)"
        )

    # Link all existing measurements that have no brew_setup_id to the default setup
    op.execute(
        f"UPDATE measurements SET brew_setup_id = '{DEFAULT_SETUP_ID}' WHERE brew_setup_id IS NULL"
    )


def downgrade() -> None:
    """Downgrade schema: remove columns and drop tables in reverse dependency order."""

    # ── Remove brew_setup_id from measurements ──
    with op.batch_alter_table("measurements", schema=None) as batch_op:
        batch_op.drop_constraint("fk_measurements_brew_setup_id", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_measurements_brew_setup_id"))
        batch_op.drop_column("brew_setup_id")

    # ── Remove new columns from beans ──
    with op.batch_alter_table("beans", schema=None) as batch_op:
        batch_op.drop_column("variety")
        batch_op.drop_column("process")
        batch_op.drop_column("roast_date")

    # ── Drop tables in reverse dependency order ──
    # (seeded data rows are deleted automatically when tables are dropped)
    op.drop_index("ix_bags_bean_id", table_name="bags")
    op.drop_table("bags")
    op.drop_table("brew_setups")
    op.drop_table("water_recipes")
    op.drop_table("papers")
    op.drop_table("brewers")
    op.drop_table("grinders")
    op.drop_table("brew_methods")

# BeanBay Schema Evolution Design

**Date:** 2026-03-21
**Status:** Approved
**Scope:** Database schema enrichment informed by Beanconqueror comparison

## Context

Comparison of BeanBay's relational schema (SQLModel/SQLite) with Beanconqueror's document-based data model revealed gaps in bean metadata, tasting axes, cupping support, purchase tracking, and frozen storage. This design addresses those gaps while preserving BeanBay's strengths (referential integrity, normalized M2M, soft deletes, reusable brew setups, append-only rating history).

Home-roasting support (green beans, roasting machines, roast profiles) is explicitly out of scope but the schema should not preclude adding it later.

## Design Decisions

- **3 distinct tasting axis sets:** BrewTaste (extraction-focused), BeanTaste (bean-character-focused), Cupping (SCAA protocol). Different purposes, different users, different scales.
- **Enums for fixed classifications, tables for user-extensible data:** BeanMixType, BeanUseType, ProcessCategory, CoffeeSpecies are enums. StorageType is a seeded lookup table.
- **Vendor is separate from Roaster:** You buy Roaster X's beans from Shop Y.
- **Cupping links to Bag (not Bean):** You cup a specific physical bag. Different bags of the same bean can taste different.
- **BeanRating gains `updated_at`:** Consistent with Cupping. History comes from multiple rows, not append-only immutability.
- **Blend percentages on the existing junction table:** No new table, just a nullable column on `bean_origins`.
- **Bean ↔ FlavorTag M2M for roaster's claimed flavors:** Separate from user tasting notes on BrewTaste/BeanTaste.
- **BrewTaste/BeanTaste have no `retired_at`:** They are 1:1 children with cascade delete from their parents (Brew/BeanRating). Soft-deleting the parent handles lifecycle. This is intentional, not a gap.
- **"Unknown" handling differs by intent:** `bean_mix_type` uses an `UNKNOWN` enum variant (every bean has a mix type, even if unspecified). `bean_use_type` uses NULL (truly optional — many beans have no intended use type labeled). The difference is semantic: "I don't know" vs "not applicable".
- **Frozen bag lifecycle:** Both `frozen_at` and `thawed_at` NULL = never frozen. `frozen_at` set, `thawed_at` NULL = currently frozen. Both set = was frozen and thawed. Re-freezing is not supported (create a new Bag instead). `bought_at` and `best_date` use `Date` (day precision is sufficient); `frozen_at`/`thawed_at` use `DateTime` (exact time matters for freshness tracking).
- **All range validations at API layer:** `roast_degree` (0-10), `percentage` (0-100), cupping axes (0-9), taste axes (0-10) are validated via Pydantic, not DB CHECK constraints. Consistent with existing pattern.
- **Migration strategy for axis rework:** The BrewTaste and BeanTaste axis changes are drop-and-add, not renames. This is a development-phase schema — no production data to preserve. The Alembic migration drops the old columns and adds the new ones.
- **All schema changes in a single Alembic migration:** One migration file for the full changeset. The schema is in early development with no production deployments.

---

## Schema Changes

### 1. Bean Model Enrichment

**Modified table: `beans`**

| New Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `roast_degree` | Float | YES | NULL | 0.0 (lightest) to 10.0 (darkest). Validated at API layer. |
| `bean_mix_type` | Enum(BeanMixType) | NO | UNKNOWN | SINGLE_ORIGIN / BLEND / UNKNOWN |
| `bean_use_type` | Enum(BeanUseType) | YES | NULL | FILTER / ESPRESSO / OMNI |
| `decaf` | Boolean | NO | False | |
| `url` | str | YES | NULL | Roaster's product page |
| `ean` | str | YES | NULL | Barcode string |

**New junction table: `bean_flavor_tags`**

| Column | Type | Notes |
|---|---|---|
| `bean_id` | UUID, FK -> beans.id | PK |
| `flavor_tag_id` | UUID, FK -> flavor_tags.id | PK |

Represents the roaster's claimed flavors from the bag label, distinct from the user's tasting notes.

### 2. Bag Model Enrichment

**Modified table: `bags`**

| New Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `bought_at` | Date | YES | NULL | Purchase date |
| `vendor_id` | UUID, FK -> vendors.id | YES | NULL | Where purchased |
| `frozen_at` | DateTime | YES | NULL | When frozen |
| `thawed_at` | DateTime | YES | NULL | When thawed (NULL = still frozen) |
| `storage_type_id` | UUID, FK -> storage_types.id | YES | NULL | Only relevant when frozen |
| `best_date` | Date | YES | NULL | Best-by / expiry date |

### 3. New Entity: Vendor

**New table: `vendors`**

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | UUID | NO | uuid4() | PK |
| `name` | str | NO | - | UNIQUE, indexed |
| `url` | str | YES | NULL | Shop website |
| `location` | str | YES | NULL | City, address, etc. |
| `notes` | str | YES | NULL | |
| `created_at` | DateTime | NO | server default | |
| `updated_at` | DateTime | NO | server default | Auto-updated on change |
| `retired_at` | DateTime | YES | NULL | Soft-delete |

### 4. New Entity: StorageType (seeded lookup)

**New table: `storage_types`**

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | UUID | NO | uuid4() | PK |
| `name` | str | NO | - | UNIQUE, indexed |
| `created_at` | DateTime | NO | server default | |
| `updated_at` | DateTime | NO | server default | Auto-updated on change |
| `retired_at` | DateTime | YES | NULL | Soft-delete |

**Seeded defaults:** Vacuum Sealed, Zip Lock, Coffee Bag, Coffee Jar, Tube

### 5. Lookup Table Enrichment

**Modified table: `origins`**

| New Column | Type | Nullable | Notes |
|---|---|---|---|
| `country` | str | YES | Structured country name |
| `region` | str | YES | Sub-region within country |

**Modified table: `process_methods`**

| New Column | Type | Nullable | Notes |
|---|---|---|---|
| `category` | Enum(ProcessCategory) | YES | WASHED / NATURAL / HONEY / ANAEROBIC / EXPERIMENTAL / OTHER |

**Modified table: `bean_varieties`**

| New Column | Type | Nullable | Notes |
|---|---|---|---|
| `species` | Enum(CoffeeSpecies) | YES | ARABICA / ROBUSTA / LIBERICA |

**Modified junction table: `bean_origins`**

| New Column | Type | Nullable | Notes |
|---|---|---|---|
| `percentage` | Float | YES | Blend component %, NULL = unknown. Validated at API layer. |

### 6. BrewTaste Axis Rework

**Modified table: `brew_tastes`**

| Column | Status | Scale |
|---|---|---|
| `score` | Kept | 0-10 |
| `acidity` | Kept | 0-10 |
| `sweetness` | Kept | 0-10 |
| `bitterness` | Kept | 0-10 |
| `body` | Kept | 0-10 |
| `balance` | **New** (replaces `intensity`) | 0-10 |
| `aftertaste` | **New** (replaces `aroma`) | 0-10 |
| `notes` | Kept | text |

Removed: `intensity`, `aroma`. These are more relevant to bean character than extraction quality.

### 7. BeanTaste Axis Rework

**Modified table: `bean_tastes`**

| Column | Status | Scale |
|---|---|---|
| `score` | Kept | 0-10 |
| `acidity` | Kept | 0-10 |
| `sweetness` | Kept | 0-10 |
| `body` | Kept | 0-10 |
| `aroma` | Kept | 0-10 |
| `complexity` | **New** (replaces `bitterness`) | 0-10 |
| `clean_cup` | **New** (replaces `intensity`) | 0-10 |
| `notes` | Kept | text |

Removed: `bitterness` (extraction issue, not bean trait), `intensity` (vague).

### 8. BeanRating Update

**Modified table: `bean_ratings`**

| New Column | Type | Notes |
|---|---|---|
| `updated_at` | DateTime, server default | Consistent with Cupping. History from multiple rows. |

### 9. New Entity: Cupping (SCAA Protocol)

**New table: `cuppings`**

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | UUID | NO | uuid4() | PK |
| `bag_id` | UUID, FK -> bags.id | NO | - | Which bag was cupped |
| `person_id` | UUID, FK -> people.id | NO | - | Who cupped it |
| `cupped_at` | DateTime | NO | - | When the session happened |
| `dry_fragrance` | Float | YES | NULL | 0-9, ground coffee aroma |
| `wet_aroma` | Float | YES | NULL | 0-9, aroma after water |
| `brightness` | Float | YES | NULL | 0-9, acidity/vibrancy |
| `flavor` | Float | YES | NULL | 0-9, overall taste quality |
| `body` | Float | YES | NULL | 0-9, weight/mouthfeel |
| `finish` | Float | YES | NULL | 0-9, aftertaste length & quality |
| `sweetness` | Float | YES | NULL | 0-9 |
| `clean_cup` | Float | YES | NULL | 0-9, absence of defects |
| `complexity` | Float | YES | NULL | 0-9, flavor layers/depth |
| `uniformity` | Float | YES | NULL | 0-9, cup-to-cup consistency |
| `cuppers_correction` | Float | YES | NULL | Personal adjustment, can be negative (-3 to +3 typical range) |
| `total_score` | Float | YES | NULL | 0-100 SCAA scale. Can be computed (sum of 10 axes) or manually entered. |
| `notes` | str | YES | NULL | |
| `created_at` | DateTime | NO | server default | |
| `updated_at` | DateTime | NO | server default | |
| `retired_at` | DateTime | YES | NULL | Soft-delete |

**New junction table: `cupping_flavor_tags`**

| Column | Type | Notes |
|---|---|---|
| `cupping_id` | UUID, FK -> cuppings.id | PK |
| `flavor_tag_id` | UUID, FK -> flavor_tags.id | PK |

---

## New Enums

| Enum | Values |
|---|---|
| **BeanMixType** | SINGLE_ORIGIN, BLEND, UNKNOWN |
| **BeanUseType** | FILTER, ESPRESSO, OMNI |
| **ProcessCategory** | WASHED, NATURAL, HONEY, ANAEROBIC, EXPERIMENTAL, OTHER |
| **CoffeeSpecies** | ARABICA, ROBUSTA, LIBERICA |

---

## Tasting Axis Comparison

| Axis | BrewTaste (0-10) | BeanTaste (0-10) | Cupping (0-9 SCAA) |
|---|---|---|---|
| score / total_score | x | x | x |
| acidity / brightness | x | x | x |
| sweetness | x | x | x |
| body | x | x | x |
| bitterness | x | - | - |
| balance | x | - | - |
| aftertaste / finish | x | - | x |
| aroma | - | x | - |
| complexity | - | x | x |
| clean_cup | - | x | x |
| dry_fragrance | - | - | x |
| wet_aroma | - | - | x |
| flavor | - | - | x |
| uniformity | - | - | x |
| cuppers_correction | - | - | x |

---

## Change Inventory

| Category | Items |
|---|---|
| **Modified entities (6)** | Bean, Bag, Origin, ProcessMethod, BeanVariety, BeanRating |
| **Reworked entities (2)** | BrewTaste, BeanTaste |
| **New entities (2)** | Vendor, Cupping |
| **New lookup table (1)** | StorageType (seeded) |
| **New junction tables (2)** | bean_flavor_tags, cupping_flavor_tags |
| **Modified junction table (1)** | bean_origins (+percentage) |
| **New enums (4)** | BeanMixType, BeanUseType, ProcessCategory, CoffeeSpecies |
| **Unchanged (18)** | people, grinders, brewers, papers, waters, water_minerals, brew_setups, brews, roasters, brew_methods, stop_modes, flavor_tags, brewer_methods, brewer_stop_modes, bean_processes, bean_varieties (junction), brew_taste_flavor_tags, bean_taste_flavor_tags |

## Out of Scope (Future)

- Home-roasting pipeline (green beans, roasting machines, roast profiles)
- TDS / refractometer integration
- Photo attachments
- Connected device / Bluetooth integrations
- Geolocation tracking on brews
- Brew field ordering / parameter visibility configuration

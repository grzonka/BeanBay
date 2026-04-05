"""Domain enums for bean and processing classification."""

from enum import StrEnum


class BeanMixType(StrEnum):
    """Whether a bean is single origin or a blend."""

    SINGLE_ORIGIN = "single_origin"
    BLEND = "blend"
    UNKNOWN = "unknown"


class BeanUseType(StrEnum):
    """Roaster's intended use for the bean."""

    FILTER = "filter"
    ESPRESSO = "espresso"
    OMNI = "omni"


class ProcessCategory(StrEnum):
    """Broad category grouping for coffee processing methods."""

    WASHED = "washed"
    NATURAL = "natural"
    HONEY = "honey"
    ANAEROBIC = "anaerobic"
    EXPERIMENTAL = "experimental"
    OTHER = "other"


class CoffeeSpecies(StrEnum):
    """Biological species of the coffee plant."""

    ARABICA = "arabica"
    ROBUSTA = "robusta"
    LIBERICA = "liberica"

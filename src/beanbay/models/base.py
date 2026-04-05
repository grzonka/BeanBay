import uuid


def uuid4_default() -> uuid.UUID:
    """Generate a new UUID4.

    Returns
    -------
    uuid.UUID
        A randomly generated UUID4.
    """
    return uuid.uuid4()

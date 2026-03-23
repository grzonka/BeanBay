"""Taskiq broker for async BayBE optimization tasks.

Uses InMemoryBroker for local/single-process deployment.
Swappable to a real broker (Redis, RabbitMQ) for production.
"""

from __future__ import annotations

from taskiq import InMemoryBroker

broker = InMemoryBroker()


@broker.task
async def generate_recommendation(job_id: str) -> None:
    """Generate a BayBE recommendation for the given optimization job.

    Parameters
    ----------
    job_id : str
        UUID string of the OptimizationJob to process.

    Notes
    -----
    Placeholder implementation. Full BayBE integration in Task 11.
    """
    pass

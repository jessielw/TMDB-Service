def webhook_failure_message(task: str, error: Exception) -> str:
    """Return an outward-safe job failure notification."""
    return (
        f"**TMDB Service:** {task} failed ({type(error).__name__}). "
        "See the local service log for details."
    )

class InvalidTokenError(Exception):
    """Raised when a provided GitHub token fails validation."""


class NotConnectedError(Exception):
    """Raised when an operation needs a stored token but none exists."""


class GithubWriteError(Exception):
    """Raised when a write to the GitHub API fails."""


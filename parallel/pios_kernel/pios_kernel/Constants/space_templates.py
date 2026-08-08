from pios_kernel.enums import SpaceSource, SpaceType

SYSTEM_SPACES = [
    {
        "name": "Health",
        "type": SpaceType.HEALTH,
        "icon": "heart",
        "color": "#22C55E",
        "source": SpaceSource.SYSTEM,
    },
    {
        "name": "Learning",
        "type": SpaceType.LEARNING,
        "icon": "book-open",
        "color": "#3B82F6",
        "source": SpaceSource.SYSTEM,
    },
    {
        "name": "Finance",
        "type": SpaceType.FINANCE,
        "icon": "wallet",
        "color": "#F59E0B",
        "source": SpaceSource.SYSTEM,
    },
    {
        "name": "Habits",
        "type": SpaceType.HABITS,
        "icon": "repeat",
        "color": "#8B5CF6",
        "source": SpaceSource.SYSTEM,
    },
    {
        "name": "Career",
        "type": SpaceType.CAREER,
        "icon": "briefcase",
        "color": "#0EA5E9",
        "source": SpaceSource.SYSTEM,
    },
]

__all__ = ["SYSTEM_SPACES"]

# PIOS Kernel

Shared domain library for the Personal Intelligence Operating System (PIOS).

## Purpose

The kernel contains the shared business language used by all PIOS services:

- Enums
- Domain models
- Value objects
- Constants and system templates

It intentionally does not contain FastAPI, SQLAlchemy, Alembic, database models,
repositories, HTTP logic, or service orchestration.

## Package layout

```text
pios_kernel/
├── Constants/
├── enums/
├── events/
├── models/
├── schemas/
├── value_objects/
└── version.py
```

Import shared concepts through package APIs:

```python
from pios_kernel.Constants import DEFAULT_PRIORITY, SYSTEM_SPACES
from pios_kernel.enums import GoalStatus, SpaceType
from pios_kernel.models import Goal, Space
from pios_kernel.value_objects import Progress
```

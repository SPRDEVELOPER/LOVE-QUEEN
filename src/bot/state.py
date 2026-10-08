from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AppState:
    settings: object
    db: object
    images: object
    limiter: object
    banned: set = field(default_factory=set)
    synced: dict = field(default_factory=dict)
    warned: dict = field(default_factory=dict)

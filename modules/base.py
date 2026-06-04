from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ModuleContext:
    config: dict
    ocr: Any
    paste: Callable[[str, dict], None]
    notify: Callable[[str], None] = print
    services: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleResult:
    module_id: str
    report_text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    actions: list[dict[str, Any]] = field(default_factory=list)


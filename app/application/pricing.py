from app.domain.enums import GenerationKind

def estimate_cost_tokens(kind: GenerationKind, *, seconds: int | None = None, resolution: str | None = None) -> int:
    if kind == GenerationKind.IMAGE:
        return 10
    base = 60
    if seconds == 10:
        base += 20
    if resolution == "1080p":
        base += 30
    return base

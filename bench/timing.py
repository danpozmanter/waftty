"""How long a benchmark run took, in words both the run and the report use."""


def duration(seconds):
    """`seconds` as hours, minutes and seconds, leaving out the leading zeros."""
    h, rest = divmod(seconds, 3600)
    m, s = divmod(rest, 60)
    return f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s" if m else f"{s}s"

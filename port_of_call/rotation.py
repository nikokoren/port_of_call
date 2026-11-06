"""Choose which harbor a multi-harbor installation shows on this refresh.

The polling URL carries the user's selection, not an installation identity, so
the backend cannot remember a per-device position. Rotation is therefore keyed
to wall-clock slots of the recipe's refresh interval: every installation with
the same selection sees the same harbor in a slot, consecutive refreshes step
through the selection in catalog order, and responses remain cacheable.
"""
import re

ROTATION_SECONDS = 15 * 60  # Matches settings.yml refresh_interval.


def parse_selection(raw, active):
    """Known IDs from a comma/whitespace list, catalog order, duplicates removed.

    Unknown IDs (for example a harbor later removed from the catalog) are
    ignored. An empty or entirely unknown selection means every harbor.
    """
    wanted = {part for part in re.split(r'[\s,]+', raw or '') if part}
    chosen = [k for k in active if k in wanted]
    return chosen or list(active)


def rotate(chosen, now, period=ROTATION_SECONDS):
    if not chosen: raise ValueError('No harbors to rotate')
    return chosen[int(now // period) % len(chosen)]

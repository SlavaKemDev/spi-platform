"""
Pure-Python KNN recommender for events.

Feature vector layout (all binary):
  indices 0-10  — categories (it, hackathon, startup, networking, lecture,
                               masterclass, games, party, sport, self_dev, dating)
  index  11     — format online
  index  12     — format offline
Total: 13 dimensions
"""

CATEGORIES = [
    'it', 'hackathon', 'startup', 'networking', 'lecture',
    'masterclass', 'games', 'party', 'sport', 'self_dev', 'dating',
]
CAT_INDEX = {c: i for i, c in enumerate(CATEGORIES)}
DIM = len(CATEGORIES) + 2  # + online + offline


def _event_vector(event):
    vec = [0.0] * DIM
    for cat in (event.categories or []):
        idx = CAT_INDEX.get(cat)
        if idx is not None:
            vec[idx] = 1.0
    fmt = event.format
    if fmt == 'online':
        vec[len(CATEGORIES)] = 1.0
    elif fmt == 'offline':
        vec[len(CATEGORIES) + 1] = 1.0
    return vec


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x * x for x in a) ** 0.5
    mag_b = sum(x * x for x in b) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _user_preference_vector(user):
    """Average feature vector over events the user has registered for."""
    from events.models import EventRegistration
    regs = EventRegistration.objects.filter(user=user).select_related('event')
    vecs = [_event_vector(r.event) for r in regs]
    if not vecs:
        return None
    n = len(vecs)
    return [sum(v[i] for v in vecs) / n for i in range(DIM)]


def _tags_to_vector(tags):
    """Build a preference vector from a list of category tag strings."""
    vec = [0.0] * DIM
    for tag in tags:
        idx = CAT_INDEX.get(tag)
        if idx is not None:
            vec[idx] = 1.0
    return vec


def recommend(user, exclude_ids=None, interest_tags=None):
    """
    Return a ranked list of (event, score) tuples for *user*, excluding
    events whose IDs are in *exclude_ids*.

    Priority for preference vector:
      1. interest_tags (explicit onboarding selection)
      2. user registration history
      3. fallback: newest registration_start first (but still all events returned)

    All reachable events are always returned — even with 0 similarity —
    so the caller always has something to show.
    """
    from django.utils import timezone
    from events.models import Event

    if exclude_ids is None:
        exclude_ids = []

    qs = Event.objects.filter(
        is_published=True,
        registration_end__gte=timezone.now(),
    ).exclude(id__in=exclude_ids).select_related('organization__university')

    # Filter university_only events
    if user.is_authenticated:
        user_uni_id = getattr(user, 'university_id', None)
        events = []
        for ev in qs:
            if ev.access_type == 'university_only':
                org_uni_id = ev.organization.university_id if ev.organization.university_id else None
                if not user_uni_id or org_uni_id != user_uni_id:
                    continue
            events.append(ev)
    else:
        events = [ev for ev in qs if ev.access_type != 'university_only']

    if not events:
        return []

    # Build preference vector
    if interest_tags:
        pref = _tags_to_vector(interest_tags)
    elif user.is_authenticated:
        pref = _user_preference_vector(user)
    else:
        pref = None

    if pref is None or all(x == 0 for x in pref):
        # No preference signal — sort by newest registration_start
        events.sort(key=lambda e: e.registration_start, reverse=True)
        return [(e, 0.0) for e in events]

    scored = [(e, _cosine(pref, _event_vector(e))) for e in events]
    # Sort by score desc; ties broken by registration_start desc
    scored.sort(key=lambda t: (t[1], t[0].registration_start.timestamp()), reverse=True)
    return scored

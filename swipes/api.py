import numpy as np
from django.utils import timezone
from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404
from ninja import Router, Schema

from events.models import *
from organizations.models import OrganizationMember
from users.models import *
from swipes.models import *

from django.forms.models import model_to_dict

router = Router(tags=["Swipes"])


class EventOut(Schema):
    id: int
    title: str
    description: str


class SwipeOut(Schema):
    id: int
    status: str
    event: EventOut


@router.post("/new", response={200: SwipeOut, 404: dict})
def new_swipe(request):
    user = request.user

    pending = EventSwipe.objects.filter(user=user, status=EventSwipe.Status.PENDING).select_related('event').first()
    if pending:
        return pending

    # find event that user not performed with

    user_history = EventSwipe.objects.filter(user=user).exclude(status=EventSwipe.Status.PENDING).select_related(
        'event')

    liked = [s.event.embedding for s in user_history if s.status == EventSwipe.Status.LIKE and s.event.embedding is not None]
    disliked = [s.event.embedding for s in user_history if s.status == EventSwipe.Status.DISLIKE and s.event.embedding is not None]

    candidates_qs = Event.objects.filter(
        is_published=True,
        registration_end__gte=timezone.now(),
        embedding__isnull=False
    ).exclude(eventswipe__user=user)

    if not candidates_qs.exists():
        return 404, {"message": "No more events"}

    candidate_events = list(candidates_qs)
    C = np.array([e.embedding for e in candidate_events])  # k * 768

    l_scores = np.zeros(len(C))
    d_scores = np.zeros(len(C))

    if liked:
        L = np.array(liked)  # n * 768
        l_scores = (C @ L.T).max(axis=1)  # C @ L.T -> k * n, max on rows -> k

    if disliked:
        D = np.array(disliked)  # m * 768
        d_scores = (C @ D.T).max(axis=1)  # C @ D.T -> k * m, max on rows -> k

    final_scores = l_scores - d_scores
    final_scores += np.random.normal(0, 0.01, size=final_scores.shape)  # add small noise to break ties

    best_id = final_scores.argmax()  # index of best candidate
    event = candidate_events[best_id]  # best candidate event

    # print top-5 candidates for debugging
    top_k = 5
    top_k_ids = np.argsort(final_scores)[-top_k:][::-1]
    print("Top candidates:")
    for idx in top_k_ids:
        print(f"Event ID: {candidate_events[idx].id}, Score: {final_scores[idx]:.4f}, L_score: {l_scores[idx]:.4f}, D_score: {d_scores[idx]:.4f}")

    event_swipe = EventSwipe.objects.create(user=user, event=event)

    return event_swipe


class SwipeRateIn(Schema):
    status: str


@router.post("/{swipe_id}/rate", response={200: SwipeRateIn, 404: dict})
def rate_swipe(request, swipe_id: int, status: str):
    user = request.user
    swipe = get_object_or_404(EventSwipe, id=swipe_id, user=user)

    if swipe.status != EventSwipe.Status.PENDING:
        return 404, {"message": "Swipe already rated"}

    if status not in [EventSwipe.Status.LIKE, EventSwipe.Status.DISLIKE]:
        return 404, {"message": "Invalid status"}

    swipe.status = status
    swipe.save(update_fields=['status'])

    return swipe

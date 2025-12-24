import random

from django.db import transaction, IntegrityError
from tripAppBE.models import Trip, TripParticipant


# ======================================================
# CONFIG
# ======================================================

MAX_CODE_ATTEMPTS = 10
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # bez O, 0, I, L


def generate_code(length=8):
    return "".join(random.choices(CODE_ALPHABET, k=length))


# ======================================================
# TRIP MANAGEMENT
# ======================================================

def create_trip(name, description, user):
    """
    Tworzy nowy trip + dodaje ownera jako uczestnika
    """
    for _ in range(MAX_CODE_ATTEMPTS):
        try:
            with transaction.atomic():
                trip = Trip.objects.create(
                    name=name,
                    description=description,
                    trip_owner=user,
                    trip_code=generate_code()
                )

                TripParticipant.objects.create(
                    trip_id=trip.trip_id,
                    user=user,
                    nickname=user.username
                )

                return {"ok": True, "trip": trip}

        except IntegrityError:
            continue

    return {"ok": False, "message": "Unique trip code was not created"}


def delete_trip(trip_id, user):
    """
    Usuwa trip – tylko owner
    """
    deleted, _ = Trip.objects.filter(
        trip_id=trip_id,
        trip_owner=user
    ).delete()

    if deleted == 0:
        return {"ok": False, "message": "Trip not found or permission denied"}

    return {"ok": True, "message": "Trip deleted"}


# ======================================================
# PARTICIPANTS
# ======================================================

def remove_participant_from_trip(trip_id, participant_id):
    deleted, _ = TripParticipant.objects.filter(
        trip_id=trip_id,
        id=participant_id
    ).delete()

    if deleted == 0:
        return {"ok": False, "message": "Participant not found"}

    return {"ok": True, "message": "Participant removed"}


def join_trip(join_code, user):
    """
    Join po Join_code placeholdera (user = NULL)
    """
    try:
        with transaction.atomic():
            participant = (
                TripParticipant.objects
                .select_for_update()
                .select_related("trip")
                .get(Join_code=join_code, user__isnull=True)
            )

            # czy user już jest w tym tripie
            if TripParticipant.objects.filter(
                trip_id=participant.trip_id,
                user_id=user.id
            ).exists():
                return {"ok": False, "message": "You already joined this trip."}

            participant.user_id = user.id
            participant.save(update_fields=["user"])

            return {
                "ok": True,
                "message": f"You successfully joined trip {participant.trip.name}"
            }

    except TripParticipant.DoesNotExist:
        return {"ok": False, "message": "Wrong or already used join code."}


# ======================================================
# QUERIES
# ======================================================

def get_trip_list(user):
    """
    Lista tripów usera
    """
    return (
        Trip.objects
        .filter(participants__user_id=user.id)
        .only("trip_id", "name", "trip_owner_id")
        .order_by("-created_at")
        .distinct()
    )


def get_trip_details(user, trip_id):
    """
    Szczegóły tripa + uczestnicy
    """
    return (
        Trip.objects
        .filter(participants__user_id=user.id, trip_id=trip_id)
        .select_related("trip_owner")
        .prefetch_related("participants__user")
        .get()
    )


# ======================================================
# PLACEHOLDERS
# ======================================================

def add_placeholder_to_trip(trip_id, nickname):
    """
    Dodaje placeholder (user = NULL) z Join_code
    """
    for _ in range(MAX_CODE_ATTEMPTS):
        try:
            with transaction.atomic():
                TripParticipant.objects.create(
                    trip_id=trip_id,
                    nickname=nickname,
                    Join_code=generate_code(),
                    user=None
                )

            return {"ok": True, "message": "Placeholder added"}

        except IntegrityError:
            continue

    return {"ok": False, "message": "Unique join code was not created"}


def remove_user_from_participant_and_regenerate_code(trip_id, participant_id):
    """
    Zamienia usera → placeholder + nowy Join_code
    """
    for _ in range(MAX_CODE_ATTEMPTS):
        try:
            with transaction.atomic():
                updated = TripParticipant.objects.filter(
                    trip_id=trip_id,
                    id=participant_id
                ).update(
                    user=None,
                    Join_code=generate_code()
                )

                if updated == 0:
                    return {"ok": False, "message": "Participant not found"}

                return {
                    "ok": True,
                    "message": "User removed, new join code generated"
                }

        except IntegrityError:
            continue

    return {"ok": False, "message": "Unique join code was not created"}

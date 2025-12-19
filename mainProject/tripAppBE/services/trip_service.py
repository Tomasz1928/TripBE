from django.db import transaction
from tripAppBE.models import Trip, UserTrip


def create_trip(name, description, user):
    try:
        with transaction.atomic():
            trip = Trip.objects.create(name=name, description=description, trip_owner=user)
            UserTrip.objects.create(trip=trip, user=user)

            return {"trip": trip, "ok": True}

    except Exception as e:
        return {"trip": None, "ok": False}


def join_trip(trip_id, user):
    try:
        with transaction.atomic():
            trip = Trip.objects.get(trip_id=trip_id)
            exists = UserTrip.objects.filter(trip=trip, user=user).exists()
            if exists:
                return {'ok': False, 'message': 'You already join to this trip.'}

            UserTrip.objects.create(trip=trip, user=user)
            return {'ok': True, 'message': f'You successfully join to trip {trip_id}'}

    except Trip.DoesNotExist:
        return {'ok': False, 'message': f'Trip with provided ID ( {trip_id} ) dont exist'}



def get_trip_list(user):
    return Trip.objects.filter(usertrip__user=user).only("trip_id", "name", "trip_owner").order_by('-created_at')


def get_trip_details(user, trip_id):
    return Trip.objects.filter(usertrip__user=user, trip_id=trip_id).prefetch_related("usertrip_set__user").get()
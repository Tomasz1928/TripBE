import graphene

from tripAppBE.models import Trip
from tripAppBE.schema.types.trip_type import TripType
from tripAppBE.services.trip_service import get_trip_details, get_trip_list
from graphql import GraphQLError


class GetTripList(graphene.ObjectType):
    trip_list = graphene.List(TripType)
    trip = graphene.Field(TripType, trip_id=graphene.ID(required=True))

    def resolve_trip_list(self, info):
        user = info.context.user
        return get_trip_list(user)

    def resolve_trip(self, info, trip_id):
        user = info.context.user

        try:
            return get_trip_details(user, trip_id)
        except Trip.DoesNotExist:
            return None

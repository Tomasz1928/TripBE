import graphene
from graphene_django import DjangoObjectType
from tripAppBE.models import Trip
from tripAppBE.schema.types.user_type import UserType


class TripType(DjangoObjectType):
    owner = graphene.Boolean()
    participants = graphene.List(UserType)

    class Meta:
        model = Trip
        fields = ("trip_id", "name", "description", "created_at", "trip_owner")

    def resolve_owner(self, info):
        return self.trip_owner_id == info.context.user.id

    def resolve_participants(self, info):
        return [ut.user for ut in self.usertrip_set.all()]
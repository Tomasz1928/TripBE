import graphene
from graphene_django import DjangoObjectType
from tripAppBE.models import Trip, TripParticipant
from tripAppBE.schema.types.user_type import UserType

class ParticipantType(graphene.ObjectType):
    id = graphene.ID()
    user = graphene.Field(UserType)
    nickname = graphene.String()
    joinCode = graphene.String()

class TripType(DjangoObjectType):
    owner = graphene.Boolean()
    owner_id = graphene.ID()
    participants = graphene.List(ParticipantType)

    class Meta:
        model = Trip
        fields = ("trip_id", "trip_code", "name", "description", "created_at", "trip_owner")

    def resolve_owner(self, info):
        return self.trip_owner_id == info.context.user.id

    def resolve_owner_id(self, info):
        return self.trip_owner_id

    def resolve_participants(self, info):
        return [
            ParticipantType(
                id=p.id,
                user=p.user,
                nickname=p.nickname,
                joinCode=p.Join_code
            )
            for p in self.participants.all()
        ]

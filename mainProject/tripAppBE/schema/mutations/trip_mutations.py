import graphene
from graphql import GraphQLError
from django.contrib.auth import get_user_model
from tripAppBE.services.trip_service import (
    create_trip,
    join_trip,
    delete_trip,
    add_placeholder_to_trip,
    remove_user_from_participant_and_regenerate_code, remove_participant_from_trip,
)

User = get_user_model()

# -------------------- Trip Mutations --------------------

class CreateTrip(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String(required=False)

    ok = graphene.Boolean()
    trip_id = graphene.ID()

    def mutate(self, info, title, description=None):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")

        result = create_trip(title, description, user)
        if result["ok"]:
            return CreateTrip(ok=True, trip_id=result["trip"].trip_id)
        return CreateTrip(ok=False, trip_id=None)


class JoinTrip(graphene.Mutation):
    class Arguments:
        join_code = graphene.String(required=True)

    ok = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, join_code):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")

        result = join_trip(join_code, user)
        return JoinTrip(ok=result["ok"], message=result["message"])


class DeleteTrip(graphene.Mutation):
    class Arguments:
        trip_id = graphene.ID(required=True)

    ok = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, trip_id):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")

        result = delete_trip(trip_id, user)
        return DeleteTrip(ok=result['ok'], message=result['message'])


# -------------------- Placeholder Mutations --------------------

class AddPlaceholder(graphene.Mutation):
    class Arguments:
        trip_id = graphene.ID(required=True)
        nickname = graphene.String(required=True)

    ok = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, trip_id, nickname):

        participant = add_placeholder_to_trip(trip_id, nickname)
        return AddPlaceholder(ok=participant['ok'], message=participant['message'])


class RemoveUserFromPlaceholder(graphene.Mutation):
    class Arguments:
        trip_id = graphene.ID(required=True)
        participant_id = graphene.ID(required=True)

    ok = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, trip_id, participant_id):
        result = remove_user_from_participant_and_regenerate_code(trip_id, participant_id)
        return RemoveUserFromPlaceholder(ok=result["ok"], message=result.get("message", "Error"))


class RemoveParticipant(graphene.Mutation):
    class Arguments:
        trip_id = graphene.ID(required=True)
        participant_id = graphene.ID(required=True)

    ok = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, trip_id, participant_id):
        result = remove_participant_from_trip(trip_id, participant_id)
        return RemoveParticipant(ok=result["ok"], message=result.get("message", "Error"))

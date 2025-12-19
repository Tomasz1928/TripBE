import graphene

from tripAppBE.services.trip_service import create_trip, join_trip


class CreateTrip(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String(required=False)

    ok = graphene.Boolean()
    trip_id = graphene.ID()

    def mutate(self, info, title, description=None):
        user = info.context.user
        result = create_trip(title, description, user)

        if result["ok"]:
            return CreateTrip(ok=True, trip_id=result["trip"].trip_id)
        return CreateTrip(ok=False, trip_id=None)


class JoinTrip(graphene.Mutation):
    class Arguments:
        tripId = graphene.ID(required=True)

    ok = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, tripId):
        user = info.context.user
        result = join_trip(tripId, user)
        return JoinTrip(ok=result['ok'], message=result['message'])



import graphene

from tripAppBE.schema.types.cost_type import CostType, SplitType, CostSumType, ParticipantPaybackType
from tripAppBE.services.cost_service import (
    get_cost_sum_for_participant_per_trip,
    get_all_cost_for_participant_per_trip,
    get_split_info_per_cost,
    get_payback_participant_relation_per_trip
)
from tripAppBE.models import TripParticipant
from graphql import GraphQLError


# --- Helper to get current participant in a trip ---
def get_current_participant(user, trip_id):
    try:
        return TripParticipant.objects.get(trip_id=trip_id, user=user)
    except TripParticipant.DoesNotExist:
        raise GraphQLError("User is not a participant in this trip.")


# -------------------- Queries --------------------

class GetCostsSumPerTrip(graphene.ObjectType):
    cost_sum = graphene.Field(
        CostSumType,
        trip_id=graphene.ID(required=True)
    )

    def resolve_cost_sum(self, info, trip_id):
        participant = get_current_participant(info.context.user, trip_id)
        total = get_cost_sum_for_participant_per_trip(participant.id, trip_id)
        return CostSumType(cost_sum=total)


class GetCostsPerTrip(graphene.ObjectType):
    costs_list = graphene.List(
        CostType,
        trip_id=graphene.ID(required=True)
    )

    def resolve_costs_list(self, info, trip_id):
        participant = get_current_participant(info.context.user, trip_id)
        return get_all_cost_for_participant_per_trip(participant.id, trip_id)


class GetSplitsInfo(graphene.ObjectType):
    splits = graphene.List(
        SplitType,
        cost_id=graphene.ID(required=True)
    )

    def resolve_splits(self, info, cost_id):
        splits = get_split_info_per_cost(cost_id)
        return [
            SplitType(
                payment=s.payment,
                split_value=s.split_value,
                to_pay_back_value=s.to_pay_back_value,
                pay_back_value=s.pay_back_value,
                participant_id=s.participant.id,
                participant_nickname=s.participant.nickname,
                payer_id=s.payer.id,
                payer_nickname=s.payer.nickname
            )
            for s in splits
        ]


class GetPayback(graphene.ObjectType):
    payback_per_trip = graphene.List(
        ParticipantPaybackType,
        trip_id=graphene.ID(required=True),
    )

    def resolve_payback_per_trip(self, info, trip_id):
        participant = get_current_participant(info.context.user, trip_id)
        paybacks = get_payback_participant_relation_per_trip(trip_id, participant.id)

        return [
            ParticipantPaybackType(
                participant_id=pb["participant"]["id"],
                nickname=pb["participant"]["nickname"],
                value=pb.get("value")
            )
            for pb in paybacks
        ]

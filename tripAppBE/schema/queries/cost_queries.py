import graphene

from tripAppBE.schema.types.cost_type import CostType, SplitType, CostSumType, UserPaybackType
from tripAppBE.services.cost_service import get_cost_sum_for_user_per_trip, get_all_cost_for_user_per_trip, \
    get_split_info_per_cost, get_payback_user_relation_per_trip


class GetCostsSumPerTrip(graphene.ObjectType):
    cost_sum = graphene.Field(
        CostSumType,
        trip_id=graphene.ID(required=True)
    )

    def resolve_cost_sum(self, info, trip_id):
        user = info.context.user
        total = get_cost_sum_for_user_per_trip(user, trip_id)
        return CostSumType(cost_sum=total)


class GetCostsPerTrip(graphene.ObjectType):
    costs_list = graphene.List(
        CostType,
        trip_id=graphene.ID(required=True)
    )

    def resolve_costs_list(self, info, trip_id):
        user = info.context.user
        return get_all_cost_for_user_per_trip(user, trip_id)


class GetSplitsInfo(graphene.ObjectType):
    splits = graphene.List(
        SplitType,
        cost_id=graphene.ID(required=True)
    )

    def resolve_splits(self, info, cost_id):
        return get_split_info_per_cost(cost_id)

class GetPayback(graphene.ObjectType):
    payback_per_trip = graphene.List(
        UserPaybackType,
        trip_id=graphene.ID(required=True),
    )

    def resolve_payback_per_trip(self, info, trip_id):
        userId = info.context.user.id
        return get_payback_user_relation_per_trip(trip_id, userId)



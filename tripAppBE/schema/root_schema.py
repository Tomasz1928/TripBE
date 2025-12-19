import graphene

from tripAppBE.schema.mutations.auth_mutations import *
from tripAppBE.schema.mutations.cost_mutation import *
from tripAppBE.schema.mutations.trip_mutations import *
from tripAppBE.schema.queries.auth_queries import AuthQuery
from tripAppBE.schema.queries.cost_queries import GetCostsPerTrip, GetCostsSumPerTrip, GetSplitsInfo, GetPayback
from tripAppBE.schema.queries.trip_queries import GetTripList


class Mutation(graphene.ObjectType):
    register_user = RegisterUser.Field()
    login_user = LoginUser.Field()
    logout_user = LogoutUser.Field()
    create_trip = CreateTrip.Field()
    join_trip = JoinTrip.Field()
    create_cost = CreateCost.Field()
    update_cost = UpdateCost.Field()
    update_payment = UpdatePayment.Field()
    delete_cost = DeleteCost.Field()
    delete_user_splits = DeleteUserSplits.Field()
    fully_settlement = FullySettlement.Field()


class Query(AuthQuery, GetCostsPerTrip, GetPayback, GetCostsSumPerTrip, GetSplitsInfo, GetTripList, graphene.ObjectType):
    pass



schema = graphene.Schema(query=Query, mutation=Mutation)

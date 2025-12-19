import graphene

from tripAppBE.schema.types.user_type import UserType


class CostType(graphene.ObjectType):
    cost_id = graphene.ID()
    cost_name = graphene.String()
    overall_value = graphene.Decimal()
    payment = graphene.Boolean()


class SplitType(graphene.ObjectType):
    payment = graphene.Boolean()
    split_value = graphene.Decimal()
    to_pay_back_value = graphene.Decimal()
    pay_back_value = graphene.Decimal()
    user = graphene.Field(UserType)
    payer = graphene.Field(UserType)

class CostSumType(graphene.ObjectType):
    cost_sum = graphene.Decimal()


class SplitInput(graphene.InputObjectType):
    user_id = graphene.ID(required=True)
    split_value = graphene.Decimal(required=True)


class UserPaybackType(graphene.ObjectType):
    user = graphene.Field(UserType)
    value = graphene.Decimal()
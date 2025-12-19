import graphene

class UserType(graphene.ObjectType):
    id = graphene.Int()
    username = graphene.String()

from django.views.decorators.csrf import csrf_exempt

from django.urls import path
from graphene_django.views import GraphQLView
from .schema import schema

urlpatterns = [
    # Other URL patterns
    path('graphql', csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=True))),
]


# from django.urls import path
# from graphene_django.views import GraphQLView
# from .schema import schema
#
# urlpatterns = [
#     # Other URL patterns
#     path('graphql', GraphQLView.as_view(schema=schema, graphiql=True)),
# ]

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTGraphQLView(GraphQLView):
    """GraphiQL is visible without a token; GraphQL operations require JWT."""

    def dispatch(self, request, *args, **kwargs):
        is_graphiql_page = request.method == "GET" and not request.GET.get("query")
        if not is_graphiql_page:
            try:
                authentication = JWTAuthentication().authenticate(request)
            except AuthenticationFailed as exc:
                return JsonResponse({"detail": str(exc)}, status=401)
            if authentication is None:
                return JsonResponse({"detail": "Authentification JWT requise."}, status=401)
            request.user, request.auth = authentication
        return super().dispatch(request, *args, **kwargs)


graphql_view = csrf_exempt(JWTGraphQLView.as_view(graphiql=True))

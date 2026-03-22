from ninja import NinjaAPI
from ninja.renderers import JSONRenderer

from users.api import router as users_router
from events.api import router as events_router
from organizations.api import router as organizations_router
from swipes.api import router as swipes_router


class UnicodeJSONRenderer(JSONRenderer):
    json_dumps_params = {"ensure_ascii": False}


api = NinjaAPI(title="UniSphere API", version="1.0", renderer=UnicodeJSONRenderer())

api.add_router("users/", users_router)
api.add_router("events/", events_router)
api.add_router("organizations/", organizations_router)
api.add_router("swipes/", swipes_router)

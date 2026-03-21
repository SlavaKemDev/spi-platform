from ninja import NinjaAPI

from users.api import router as users_router

api = NinjaAPI(title="СПИ API", version="1.0")

api.add_router("users/", users_router)

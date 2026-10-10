from fastapi import APIRouter

from . import auth, materials, assets, authors, categories, tags, library, reading_lists, reading_progress, bookmarks, user_tags, notes, suggestions, admin

api_router = APIRouter()

@api_router.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(materials.router, prefix="/materials", tags=["materials"])
api_router.include_router(assets.router, tags=["assets"])
api_router.include_router(authors.router, prefix="/authors", tags=["authors"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(library.router, tags=["library"])
api_router.include_router(reading_lists.router, tags=["reading_lists"])
api_router.include_router(reading_progress.router, tags=["reading_progress"])
api_router.include_router(bookmarks.router, tags=["bookmarks"])
api_router.include_router(user_tags.router, tags=["user_tags"])
api_router.include_router(notes.router, tags=["notes"])
api_router.include_router(suggestions.router, tags=["suggestions"])
api_router.include_router(admin.router, tags=["admin"])

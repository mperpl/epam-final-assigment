from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import auth, documents, projects
from app.core.exceptions import AppException
from app.core.lifespan import lifespan

app = FastAPI(lifespan=lifespan)

@app.exception_handler(AppException)
async def global_app_exception_handler(request: Request, exception: AppException):
    return JSONResponse(status_code=exception.status_code, content={"detail": exception.message})

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(documents.router)
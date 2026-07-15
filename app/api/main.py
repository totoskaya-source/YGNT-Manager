from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="YGNT Manager API",
    version="1.1.0",
    description="API officielle de YGNT Manager"
)

# Templates HTML
templates = Jinja2Templates(directory="app/web/templates")

# Fichiers statiques (CSS, JS, images)
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "YGNT Manager",
            "version": "1.1.0"
        }
    )


@app.get("/health")
def health():
    return {"status": "healthy"}

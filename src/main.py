from fastapi import FastAPI

from dotenv import load_dotenv

from epic.routes import router as epic_generator_route
from project.routes import router as project_management_route
load_dotenv()

app = FastAPI(
    title="Project Management Agent API",
    description="AI Agent for classifying tasks into epics and stories",
    version="0.1.0"
)

app.include_router(epic_generator_route, prefix="/epic_generator")
app.include_router(project_management_route, prefix="/project_management")

@app.get("/health")
async def health_check():
    """
    health check   
    """
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Project Management Agent API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        reload_dirs=["src"]
    )
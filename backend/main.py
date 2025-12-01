from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from .services import GitHubService, GroqService
from .analysis import AnalysisService
from .docgen import DocGenService
import os

app = FastAPI(title="ReEngineDoc Assistant API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
github_service = GitHubService()
groq_service = GroqService()
analysis_service = AnalysisService()
docgen_service = DocGenService()

class GenerateRequest(BaseModel):
    repo_url: str
    diagram_type: str = "class" # class, sequence, usecase

@app.post("/generate/adr")
async def generate_adr(request: GenerateRequest):
    try:
        commits = github_service.fetch_commits(request.repo_url)
        adr_content = groq_service.generate_adr(commits)
        return {"content": adr_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/srs")
async def generate_srs(request: GenerateRequest):
    try:
        # Fetch all relevant files for analysis
        # For MVP, we'll fetch a subset or just the structure + key files
        # This is a simplification. In a real app, we'd need to clone or fetch recursively.
        # Here we will just fetch the file structure and maybe README
        file_structure = github_service.fetch_file_structure(request.repo_url)
        files_to_analyze = {}
        
        # Simple heuristic: fetch content of up to 5 Python/JS/Java files to analyze
        # This avoids hitting API limits too hard for MVP
        files_list = file_structure.split('\n')
        count = 0
        for f in files_list:
            if count >= 5: break
            if f.endswith(('.py', '.js', '.java')):
                try:
                    content = github_service.fetch_file_content(request.repo_url, f)
                    files_to_analyze[f] = content
                    count += 1
                except:
                    continue
        
        analysis_data = analysis_service.parse_codebase(files_to_analyze)
        
        try:
            readme_content = github_service.fetch_file_content(request.repo_url, "README.md")
        except:
            readme_content = "No README found."
            
        srs_content = groq_service.generate_srs(analysis_data, readme_content)
        return {"content": srs_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/diagram")
async def generate_diagram(request: GenerateRequest):
    try:
        # Similar logic to SRS: fetch and analyze
        file_structure = github_service.fetch_file_structure(request.repo_url)
        files_to_analyze = {}
        files_list = file_structure.split('\n')
        count = 0
        for f in files_list:
            if count >= 5: break
            if f.endswith(('.py', '.js', '.java')):
                try:
                    content = github_service.fetch_file_content(request.repo_url, f)
                    files_to_analyze[f] = content
                    count += 1
                except:
                    continue
                    
        analysis_data = analysis_service.parse_codebase(files_to_analyze)
        diagram_code = groq_service.generate_diagram(analysis_data, request.diagram_type)
        diagram_code = diagram_code.replace("```mermaid", "").replace("```", "").strip()
        return {"content": diagram_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DownloadRequest(BaseModel):
    content: str
    filename: str

@app.post("/download/word")
async def download_word(request: DownloadRequest):
    try:
        buffer = docgen_service.create_word_doc(request.content, request.filename.replace(".docx", ""))
        headers = {
            'Content-Disposition': f'attachment; filename="{request.filename}"'
        }
        return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"message": "ReEngineDoc Assistant API is running"}

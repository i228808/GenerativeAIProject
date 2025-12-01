from fastapi import FastAPI, HTTPException, Response, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import requests

from .services import GitHubService, GroqService
from .analysis import AnalysisService
from .docgen import DocGenService
from .database import SessionLocal, engine, Base
from .models import Document as DocumentModel
import os

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ReEngineDoc Assistant API")

# OAuth2 Scheme (Optional for now, just to extract token from header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

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

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class GenerateRequest(BaseModel):
    repo_url: str
    diagram_type: str = "class"

class DocumentResponse(BaseModel):
    id: int
    repo_url: str
    doc_type: str
    created_at: str
    
    class Config:
        orm_mode = True

def save_document(db: Session, repo_url: str, doc_type: str, content: str):
    db_doc = DocumentModel(repo_url=repo_url, doc_type=doc_type, content=content)
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

# Auth Endpoints
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

@app.get("/auth/login")
async def login():
    return {
        "url": f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=repo"
    }

@app.get("/auth/callback")
async def callback(code: str):
    url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get token")
    
    token_data = response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token found")
    
    return {"access_token": access_token}

@app.post("/generate/adr")
async def generate_adr(request: GenerateRequest, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        # oauth2_scheme returns the token string if present
        commits = github_service.fetch_commits(request.repo_url, access_token=token)
        adr_content = groq_service.generate_adr(commits)
        save_document(db, request.repo_url, "adr", adr_content)
        return {"content": adr_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/srs")
async def generate_srs(request: GenerateRequest, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        file_structure = github_service.fetch_file_structure(request.repo_url, access_token=token)
        files_to_analyze = {}
        files_list = file_structure.split('\n')
        count = 0
        for f in files_list:
            if count >= 5: break
            if f.endswith(('.py', '.js', '.java')):
                try:
                    content = github_service.fetch_file_content(request.repo_url, f, access_token=token)
                    files_to_analyze[f] = content
                    count += 1
                except:
                    continue
        
        analysis_data = analysis_service.parse_codebase(files_to_analyze)
        
        try:
            readme_content = github_service.fetch_file_content(request.repo_url, "README.md", access_token=token)
        except:
            readme_content = "No README found."
            
        srs_content = groq_service.generate_srs(analysis_data, readme_content)
        save_document(db, request.repo_url, "srs", srs_content)
        return {"content": srs_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/diagram")
async def generate_diagram(request: GenerateRequest, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        file_structure = github_service.fetch_file_structure(request.repo_url, access_token=token)
        files_to_analyze = {}
        files_list = file_structure.split('\n')
        count = 0
        for f in files_list:
            if count >= 5: break
            if f.endswith(('.py', '.js', '.java')):
                try:
                    content = github_service.fetch_file_content(request.repo_url, f, access_token=token)
                    files_to_analyze[f] = content
                    count += 1
                except:
                    continue
                    
        analysis_data = analysis_service.parse_codebase(files_to_analyze)
        diagram_code = groq_service.generate_diagram(analysis_data, request.diagram_type)
        diagram_code = diagram_code.replace("```mermaid", "").replace("```", "").strip()
        
        save_document(db, request.repo_url, f"diagram_{request.diagram_type}", diagram_code)
        return {"content": diagram_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", response_model=List[DocumentResponse])
async def list_documents(db: Session = Depends(get_db)):
    docs = db.query(DocumentModel).order_by(DocumentModel.created_at.desc()).limit(10).all()
    # Convert datetime to string for simple JSON response
    return [
        {
            "id": d.id,
            "repo_url": d.repo_url,
            "doc_type": d.doc_type,
            "created_at": d.created_at.isoformat()
        } 
        for d in docs
    ]

@app.get("/documents/{doc_id}")
async def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"content": doc.content, "doc_type": doc.doc_type}

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

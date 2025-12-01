import os
import requests
from groq import Groq
from typing import List, Dict, Optional
from dotenv import load_dotenv

from pathlib import Path

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

class GitHubService:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.headers = {"Authorization": f"token {self.token}"} if self.token else {}
        self.base_url = "https://api.github.com"

    def _get_repo_details(self, repo_url: str):
        # Extract owner and repo from URL (e.g., https://github.com/owner/repo)
        parts = repo_url.rstrip("/").split("/")
        return parts[-2], parts[-1]

    def fetch_commits(self, repo_url: str, limit: int = 20) -> List[Dict]:
        owner, repo = self._get_repo_details(repo_url)
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params = {"per_page": limit}
        
        try:
            if self.api_key:
                self.client = Groq(api_key=self.api_key)
            else:
                self.client = None
                print("Warning: GROQ_API_KEY not found. Generation will fail.")
        except Exception as e:
            self.client = None
            print(f"Error initializing Groq client: {e}")

    def generate_adr(self, commits: List[Dict]) -> str:
        if not self.client:
            return "Error: GROQ_API_KEY not configured."
        
        commits_text = "\n".join([f"- {c['date']}: {c['message']}" for c in commits])
        prompt = f"""
        Analyze the following Git commit history and generate an Architectural Decision Record (ADR).
        Focus on significant architectural changes, design decisions, or important refactors.
        
        Commits:
        {commits_text}
        
        Output Format (Markdown):
        # Title
        ## Status
        ## Context
        ## Decision
        ## Consequences
        """
        return self._call_llm(prompt)

    def generate_srs(self, analysis_data: Dict[str, Any], readme_content: str = "") -> str:
        if not self.client:
            return "Error: GROQ_API_KEY not configured."

        # Summarize analysis data for prompt to avoid token limits
        classes_summary = [f"{c['name']} (File: {c['file']})" for c in analysis_data.get('classes', [])]
        functions_summary = [f"{f['name']} (File: {f['file']})" for f in analysis_data.get('functions', [])]
        
        prompt = f"""
        Generate a Software Requirements Specification (SRS) based on the following codebase analysis.
        
        Context (README):
        {readme_content[:2000]}
        
        Codebase Structure:
        Classes: {', '.join(classes_summary[:50])}
        Functions: {', '.join(functions_summary[:50])}
        
        Output Format (Markdown):
        # Introduction
        # Functional Requirements
        # Non-Functional Requirements
        # System Architecture
        # Data Models
        """
        return self._call_llm(prompt)

    def generate_diagram(self, analysis_data: Dict[str, Any], diagram_type: str = "class") -> str:
        if not self.client:
            return "Error: GROQ_API_KEY not configured."

        classes_summary = [f"Class {c['name']} inherits {c['bases']}" for c in analysis_data.get('classes', [])]
        relationships = [f"{r['source']} calls {r['target']}" for r in analysis_data.get('relationships', [])]

        prompt = f"""
        Generate a Mermaid.js {diagram_type} Diagram based on the following code analysis.
        
        Classes:
        {json.dumps(classes_summary, indent=2)}
        
        Relationships:
        {json.dumps(relationships, indent=2)}
        
        Output ONLY the Mermaid code inside a ```mermaid``` block.
        """
        return self._call_llm(prompt)

    def _call_llm(self, prompt: str) -> str:
        if not self.client:
            return "Error: GROQ_API_KEY not configured."
            
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert software architect and technical writer."},
                {"role": "user", "content": prompt}
            ],
            model=self.model,
        )
        return chat_completion.choices[0].message.content

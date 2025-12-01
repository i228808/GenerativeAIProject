import ast
import re
from typing import List, Dict, Any

class AnalysisService:
    def parse_codebase(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Parses a dictionary of {filename: content} and returns structured analysis data.
        """
        analysis_results = {
            "classes": [],
            "functions": [],
            "relationships": []
        }

        for filename, content in files.items():
            if filename.endswith(".py"):
                self._parse_python(filename, content, analysis_results)
            elif filename.endswith(".js") or filename.endswith(".jsx") or filename.endswith(".ts") or filename.endswith(".tsx"):
                self._parse_javascript(filename, content, analysis_results)
            elif filename.endswith(".java"):
                self._parse_java(filename, content, analysis_results)
        
        return analysis_results

    def _parse_python(self, filename: str, content: str, results: Dict[str, Any]):
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    results["classes"].append({
                        "name": node.name,
                        "file": filename,
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                        "bases": [b.id for b in node.bases if isinstance(b, ast.Name)]
                    })
                elif isinstance(node, ast.FunctionDef):
                    # Only add top-level functions or handle differently if needed
                    # For now, we might just track them if they are not in a class (simplification)
                    pass
                
                # Basic relationship extraction (calls)
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        results["relationships"].append({
                            "source": filename,
                            "target": node.func.id,
                            "type": "call"
                        })
        except SyntaxError:
            print(f"Failed to parse Python file: {filename}")

    def _parse_javascript(self, filename: str, content: str, results: Dict[str, Any]):
        # Regex-based parsing for JS classes and functions
        class_pattern = re.compile(r'class\s+(\w+)(?:\s+extends\s+(\w+))?')
        method_pattern = re.compile(r'(\w+)\s*\(') # Simplified method detection

        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            base_class = match.group(2)
            results["classes"].append({
                "name": class_name,
                "file": filename,
                "methods": [], # Hard to extract methods reliably with regex inside class block without state
                "bases": [base_class] if base_class else []
            })
        
        # Function definitions (simplified)
        function_pattern = re.compile(r'function\s+(\w+)')
        for match in function_pattern.finditer(content):
             results["functions"].append({
                "name": match.group(1),
                "file": filename
            })

    def _parse_java(self, filename: str, content: str, results: Dict[str, Any]):
        # Regex-based parsing for Java classes
        class_pattern = re.compile(r'public\s+class\s+(\w+)(?:\s+extends\s+(\w+))?')
        
        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            base_class = match.group(2)
            results["classes"].append({
                "name": class_name,
                "file": filename,
                "methods": [], 
                "bases": [base_class] if base_class else []
            })

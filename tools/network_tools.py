from typing import List, Dict, Any
from langchain_core.tools import tool
import requests
import re
import json
from langchain_openai import ChatOpenAI
from .common import log_progress

@tool
def find_endpoints(js_url: str) -> List[str]:
    """Finds API endpoints in JavaScript code."""
    log_progress("Searching for endpoints in JavaScript code...")
    try:
        response = requests.get(js_url)
        js_content = response.text
        
        patterns = [
            r'["\']/(api/[^"\']*)["\']',
            r':\s*["\']/(api/[^"\']*)["\']',
            r'fetch\(["\']/(api/[^"\']*)["\']',
        ]
        
        endpoints = []
        for pattern in patterns:
            matches = re.findall(pattern, js_content)
            endpoints.extend(matches)
            
        unique_endpoints = list(set(endpoints))
        log_progress(f"Found {len(unique_endpoints)} unique endpoints: {', '.join(unique_endpoints)}")
        return unique_endpoints
    except Exception as e:
        log_progress(f"❌ Error finding endpoints: {str(e)}")
        return []

@tool
def analyze_js_for_requirements(js_url: str, endpoint: str) -> Dict[str, Any]:
    """Analyzes JavaScript code to understand endpoint requirements."""
    log_progress(f"Analyzing JavaScript code for {endpoint} requirements...")
    
    try:
        response = requests.get(js_url)
        js_content = response.text
        
        llm = ChatOpenAI(
            temperature=0,
            model="gpt-4"
        )
        
        analysis_prompt = f"""
        Analyze this JavaScript code and tell me what's required to access the endpoint {endpoint}.
        Look for:
        1. Required headers
        2. Specific values or secrets
        3. Authentication methods
        4. Any other requirements
        
        JavaScript code:
        {js_content}
        
        Provide your response as a JSON object with these keys:
        - headers: object of required headers and their values
        - auth_type: type of authentication if any
        - secrets: any hardcoded secrets found
        - notes: additional observations for {endpoint} ONLY
        """
        
        response = llm.invoke(analysis_prompt)
        requirements = json.loads(response.content)
        
        log_progress(f"Requirements analysis for {endpoint}:")
        for key, value in requirements.items():
            if value:  # Only log non-empty values
                log_progress(f"  • {key}: {value}")
        
        return requirements
    except Exception as e:
        log_progress(f"❌ Error analyzing requirements: {str(e)}")
        return {"error": str(e)} 
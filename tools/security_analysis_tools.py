from typing import Dict, Any
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import json
import subprocess
from .common import log_progress

@tool
def analyze_security_response(response: str) -> Dict[str, Any]:
    """Analyzes a response for security issues."""
    log_progress("Analyzing response for security vulnerabilities...")
    
    try:
        llm = ChatOpenAI(
            temperature=0,
            model="gpt-4"
        )
        
        analysis_prompt = """
        Analyze this HTTP response for security vulnerabilities:
        ```
        """ + response + """
        ```

        Look for:
        1. Sensitive data exposure (SSNs, API keys, credentials)
        2. Authentication issues (missing auth, weak auth)
        3. Authorization issues (improper access controls)
        4. Information disclosure in error messages
        5. Response headers security issues
        6. PII disclosure (names, addresses, phone numbers, etc.)

        Return your analysis as a JSON object with these keys (do NOT use markdown formatting):
        {
            "vulnerability": <vulnerability_name>,
            "recommendations": <list of fix suggestions>
        }"""
        
        response_content = llm.invoke(analysis_prompt).content
        
        # Clean the response content
        if "```json" in response_content:
            response_content = response_content.split("```json")[1].split("```")[0]
        elif "```" in response_content:
            response_content = response_content.split("```")[1].split("```")[0]
            
        response_content = response_content.strip()
        analysis = json.loads(response_content)
        
        if analysis.get('vulnerability'):
            log_progress("Vuln Found:")
            log_progress(f"  ⚠️  {analysis['vulnerability']}")
        else:
            log_progress("No immediate vulnerabilities found.")
        
        return analysis
    except Exception as e:
        log_progress(f"❌ Error analyzing response: {str(e)}")
        return {"error": str(e)}

@tool
def execute_security_test(endpoint: str, base_url: str, requirements: Dict[str, Any]) -> str:
    """
    Uses LLM to craft and execute security tests based on analyzed requirements.
    """
    log_progress(f"Starting security test execution for {endpoint}")
    log_progress(f"Base URL: {base_url}")
    log_progress(f"Requirements: {json.dumps(requirements, indent=2)}")
    
    try:
        llm = ChatOpenAI(
            temperature=0,
            model="gpt-4"
        )
        
        # Ask LLM to craft the test request
        craft_prompt = f"""
        Based on these requirements for endpoint {endpoint}:
        {json.dumps(requirements, indent=2)}

        Craft a curl command that would test this endpoint. Consider:
        1. If authentication is required
        2. Any specific header values found
        3. Any secrets or tokens discovered
        4. The most likely vulnerabilities

        Format the response as a JSON object with:
        - method: HTTP method to use
        - headers: dictionary of headers to include
        - notes: why you chose these test values

        DO NOT include the actual curl command in your response."""
        
        test_config = json.loads(llm.invoke(craft_prompt).content)
        log_progress(f"Test configuration generated: {json.dumps(test_config, indent=2)}")
        
        # Build and execute curl command
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        cmd = ['curl', '-i', '-s', '-X', test_config['method']]
        
        for key, value in test_config['headers'].items():
            cmd.extend(['-H', f'{key}: {value}'])
        
        cmd.append(url)
        
        log_progress(f"Executing curl command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.stdout:
            log_progress(f"Response received - Status: {result.stdout.split()[1] if ' ' in result.stdout else 'unknown'}")
            log_progress(f"Response: {result.stdout}")
        else:
            log_progress("No response received from the server")
            
        if result.stderr:
            log_progress(f"Errors during execution: {result.stderr}")
        
        return result.stdout
        
    except Exception as e:
        log_progress(f"❌ Test failed: {str(e)}")
        return f"Error: {str(e)}" 
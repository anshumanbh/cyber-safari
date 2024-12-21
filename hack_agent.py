from typing import List, Dict, Any, Optional
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
import requests
import json
import re
import subprocess
from datetime import datetime

def log_progress(message: str):
    """Helper function to log progress with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] 🔍 {message}")

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

    print("\n" + "=" * 50)
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
            "severity": <severity_level>,
            "recommendations": <list of fix suggestions>
        }

        Example response:
        {
            "vulnerability": "Sensitive data exposure in response",
            "severity": "high",
            "recommendations": ["Implement proper authentication", "Remove sensitive data from response"]
        }"""
        
        response_content = llm.invoke(analysis_prompt).content
        
        # Clean the response content
        if "```json" in response_content:
            response_content = response_content.split("```json")[1].split("```")[0]
        elif "```" in response_content:
            response_content = response_content.split("```")[1].split("```")[0]
            
        response_content = response_content.strip()
        
        # log_progress(f"Cleaned response content: {response_content}")
        
        analysis = json.loads(response_content)
        
        if analysis.get('vulnerability'):
            log_progress("Vuln Found:")
            log_progress(f"  ⚠️  [{analysis['severity'].upper()}] {analysis['vulnerability']}")
        else:
            log_progress("No immediate vulnerabilities found.")
        
        return analysis
    except json.JSONDecodeError as e:
        log_progress(f"❌ Error parsing LLM response: {str(e)}")
        log_progress(f"Problematic content: {response_content}")
        return {
            "vulnerability": "Error analyzing response",
            "severity": "unknown",
            "recommendations": ["Manual analysis recommended"]
        }
    except Exception as e:
        log_progress(f"❌ Error analyzing response: {str(e)}")
        return {"error": str(e)}

@tool
def execute_security_test(endpoint: str, base_url: str, requirements: Dict[str, Any]) -> str:
    """
    Uses LLM to craft and execute security tests based on analyzed requirements.
    Args:
        endpoint: API endpoint to test
        base_url: Base URL for the target
        requirements: Dictionary containing analyzed requirements from JS
    Returns:
        Test results
    """
    log_progress(f"Crafting security test for {endpoint} based on requirements")
    
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
        
        log_progress(f"Executing test for {endpoint} with curl command: {cmd}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        log_progress(f"Response: {result.stdout}")
        log_progress(f"Test completed - Status: {result.stdout.split()[1] if ' ' in result.stdout else 'unknown'}")
        
        return result.stdout
        
    except Exception as e:
        log_progress(f"❌ Test failed: {str(e)}")
        return f"Error: {str(e)}"

def create_security_agent():
    """Creates and returns a ReAct agent for security testing"""
    tools = [
        find_endpoints,
        analyze_js_for_requirements,
        execute_security_test,
        analyze_security_response
    ]
    
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4"  # or any other model name
    )
    llm_with_system = llm.bind(
        system_message="""
        You are a security testing agent. Follow these steps PRECISELY:

1. Find all endpoints using find_endpoints

2. For EACH endpoint found:
   a) First use analyze_js_for_requirements to find requirements
   b) Then execute_security_test with discovered requirements
   c) Use analyze_security_response on the response
   
Remember: Actually execute tests with discovered values!"""
    )
    
    return create_react_agent(
        tools=tools,
        model=llm_with_system
    )

def main(js_url: str, base_url: str):
    print("\n🔒 Starting Security Analysis 🔒")
    print("=" * 50)
    
    agent = create_security_agent()
    
    initial_message = HumanMessage(
        content=f"""Analyze and test {js_url} for security vulnerabilities."""
    )
    
    try:
        result = agent.invoke({
            "messages": [initial_message],
            "config": {"recursion_limit": 50}
        })

        # Extract security findings
        findings = []
        for msg in result["messages"]:
            if (hasattr(msg, 'content') and msg.content and 
                isinstance(msg.content, str) and
                ("vulnerability" in msg.content.lower() or 
                 "vulnerabilities" in msg.content.lower() or
                 "security analysis" in msg.content.lower())):
                findings.append(msg.content)
        
        print("\n" + "=" * 50)
        print("🏁 Security Analysis Complete!")
        print("=" * 50)
        
        # if findings:
        #     print("\n📝 Security Findings:")
        #     for finding in findings:
        #         print("-" * 50)
        #         print(finding)
        #         print()
            
            # # Print a clear summary of all findings
            # print("\n🔍 Summary of All Findings:")
            # print("=" * 50)
            # for finding in findings:
            #     if "Endpoint:" in finding:
            #         endpoint = finding.split("Endpoint:")[1].split("\n")[0].strip()
            #         vulnerabilities = [line.strip() for line in finding.split("\n") if "Vulnerability:" in line]
            #         severity = [line.strip() for line in finding.split("\n") if "Severity:" in line]
            #         print(f"\n• {endpoint}")
            #         for vuln in vulnerabilities:
            #             print(f"  - {vuln}")
            #         for sev in severity:
            #             print(f"  - {sev}")
        # else:
        #     print("\n⚠️ No security findings were generated.")
        
        return {
            "status": "success",
            "messages": result["messages"],
            "findings": findings
        }
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "messages": []
        }

if __name__ == "__main__":
    js_url = "http://localhost:5000/main.js"
    base_url = "http://localhost:5000"
    result = main(js_url, base_url)

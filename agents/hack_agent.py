from typing import List, Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from tools.network_tools import find_endpoints, analyze_js_for_requirements
from tools.security_analysis_tools import analyze_security_response, execute_security_test
from tools.common import log_progress

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
        model="gpt-4"
    )
    llm_with_system = llm.bind(
        system_message="""You are a security testing agent. You MUST follow this EXACT format for your analysis:

INITIAL STEPS:
1. First call: find_endpoints(js_url)
2. Store the list of endpoints

FOR EACH ENDPOINT:
1. Call: analyze_js_for_requirements(js_url, current_endpoint)
2. Store the requirements object
3. Call: execute_security_test(
   - endpoint: current_endpoint,
   - base_url: from initial message,
   - requirements: complete requirements object from step 1
   )
4. Store the response
5. Call: analyze_security_response(response from step 3)
6. Summarize findings

YOU MUST USE THIS EXACT THOUGHT FORMAT:
Thought: I will analyze each endpoint systematically.
Action: find_endpoints
Action Input: {"js_url": "the_js_url"}
Observation: [List of endpoints found]

For each endpoint:
Thought: Analyzing requirements for endpoint {endpoint}
Action: analyze_js_for_requirements
Action Input: {"js_url": "the_js_url", "endpoint": "current_endpoint"}
Observation: [Requirements object]

Thought: Executing security test with the discovered requirements
Action: execute_security_test
Action Input: {
    "endpoint": "current_endpoint",
    "base_url": "the_base_url",
    "requirements": [EXACT requirements object from previous step]
}
Observation: [Test response]

Thought: Analyzing the security implications of the response
Action: analyze_security_response
Action Input: {"response": "test_response"}
Observation: [Security analysis]

REPEAT FOR EACH ENDPOINT.

Final Thought: Summarize all findings.

IMPORTANT:
- NEVER skip steps
- ALWAYS use the exact thought format
- ALWAYS pass the complete requirements object
- ALWAYS execute tests for every endpoint
- ALWAYS analyze every response"""
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
        content=f"""Security Test Request:
- JavaScript URL: {js_url}
- Base URL: {base_url}

You must test ALL endpoints found in the JavaScript file.
For each endpoint:
1. Find its requirements
2. Execute security tests
3. Analyze the responses

Report any security vulnerabilities found."""
    )
    
    try:
        result = agent.invoke({
            "messages": [initial_message],
            "config": {
                "recursion_limit": 50,
                "max_iterations": 100  # Increased to ensure all endpoints are tested
            }
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
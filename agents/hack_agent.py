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
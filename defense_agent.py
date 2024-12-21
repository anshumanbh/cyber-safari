from typing import List, Dict, Any
from langchain_core.tools import BaseTool, tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
import json
from datetime import datetime
from security_tool import init_security_tool

def log_progress(message: str):
    """Helper function to log progress with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] 🛡️ {message}")

@tool
def analyze_logs(log_content: str) -> Dict[str, Any]:
    """
    Analyzes application logs to identify potential security attacks.
    
    Args:
        log_content: String containing application logs
        
    Returns:
        Dictionary containing identified attack patterns and details
    """
    log_progress("Analyzing application logs for attack patterns...")
    
    try:
        llm = ChatOpenAI(
            temperature=0,
            model="gpt-4"
        )
        
        analysis_prompt = f"""
        Analyze these application logs for potential security attacks:
        ```
        {log_content}
        ```
        Identify:
        1. Type of attack being attempted
        2. Target endpoints or resources
        3. Attack patterns or indicators
        4. Potential vulnerabilities being exploited
        
        Format your response as a JSON object with these keys:
        - attack_type: identified type of attack
        - target: targeted endpoint or resource
        - indicators: list of attack indicators found
        - vulnerability: potential vulnerability being exploited
        - evidence: relevant log entries that support this analysis
        """
        
        response = llm.invoke(analysis_prompt)
        print("=" * 50)
        log_progress(f"Analysis: {response.content}")
        print("=" * 50)
        analysis = json.loads(response.content)
        
        log_progress(f"Identified {analysis['attack_type']} attack targeting {analysis['target']}")
        print("=" * 50)
        
        return analysis
        
    except Exception as e:
        log_progress(f"❌ Error analyzing logs: {str(e)}")
        return {"error": str(e)}

@tool
def identify_security_controls(attack_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determines appropriate security controls based on attack analysis.
    
    Args:
        attack_analysis: Dictionary containing attack analysis details
        
    Returns:
        Dictionary containing recommended security controls
    """
    log_progress(f"Identifying security controls for {attack_analysis['attack_type']} attack...")
    
    try:
        # Initialize security knowledge base tool
        security_kb = init_security_tool()
        
        # Craft query based on attack analysis
        query = f"""
        How to protect against {attack_analysis['attack_type']} attacks 
        targeting {attack_analysis['target']} where {attack_analysis['vulnerability']} 
        is being exploited?
        """
        log_progress(f"Query: {query}")
        print("=" * 50)
        
        # Query knowledge base
        controls = security_kb.invoke({"query": query})

        log_progress(f"Found {len(controls['results'])} relevant security controls")
        log_progress(f"Controls: {controls['results']}")
        print("=" * 50)

        return {
            "attack_analysis": attack_analysis,
            "security_controls": controls['results']
        }
        
    except Exception as e:
        log_progress(f"❌ Error identifying controls: {str(e)}")
        return {"error": str(e)}

@tool
def generate_recommendations(security_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates specific recommendations for implementing security controls.
    
    Args:
        security_info: Dictionary containing attack analysis and security controls
        
    Returns:
        Dictionary containing implementation recommendations
    """
    log_progress("Generating security control recommendations...")
    print("=" * 50)
    
    try:
        llm = ChatOpenAI(
            temperature=0,
            model="gpt-4"
        )
        
        recommendations_prompt = f"""
        Based on this security information:
        Attack Analysis: {json.dumps(security_info['attack_analysis'], indent=2)}
        Security Controls: {json.dumps(security_info['security_controls'], indent=2)}
        
        Generate specific recommendations for implementing security controls to prevent this attack.
        
        Include:
        1. Prioritized list of actions to take
        2. Any Configuration changes that might be needed
        
        Format your response as a JSON object with these keys:
        - immediate_actions: list of high-priority actions
        - configuration_changes: required configuration updates
        """
        
        log_progress(f"Recommendations Prompt: {recommendations_prompt}")
        print("=" * 50)

        response = llm.invoke(recommendations_prompt)
        recommendations = json.loads(response.content)
        
        log_progress(f"Recommendations: {recommendations}")
        print("=" * 50)
        
        return recommendations
        
    except Exception as e:
        log_progress(f"❌ Error generating recommendations: {str(e)}")
        return {"error": str(e)}

def create_defensive_agent():
    """Creates and returns a ReAct agent for defensive security analysis"""
    tools = [
        analyze_logs,
        identify_security_controls,
        generate_recommendations
    ]
    
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4"
    )
    
    llm_with_system = llm.bind(
        system_message="""You are a defensive security agent. Follow these steps PRECISELY:

1. First analyze the logs using analyze_logs to identify attacks
2. For each identified attack:
   a) Use identify_security_controls to find relevant security measures
   b) Use generate_recommendations to create specific implementation plans
   
Remember to focus on actionable defensive measures!"""
    )
    
    return create_react_agent(
        tools=tools,
        model=llm_with_system  # Changed from llm to model
    )

def main(log_content: str):
    print("\n🛡️ Starting Defensive Security Analysis 🛡️")
    print("=" * 50)
    
    agent = create_defensive_agent()
    
    initial_message = HumanMessage(
        content=f"""Analyze these application logs for security threats and recommend defenses:
        
        {log_content}"""
    )
    
    try:
        result = agent.invoke({
            "messages": [initial_message],
            "config": {"recursion_limit": 50}
        })
        
        # Extract recommendations
        recommendations = []
        for msg in result["messages"]:
            if (hasattr(msg, 'content') and msg.content and 
                isinstance(msg.content, str) and
                ("recommendation" in msg.content.lower() or 
                 "security control" in msg.content.lower())):
                recommendations.append(msg.content)
        
        if recommendations:
            print("\n📝 Security Recommendations:")
            for rec in recommendations:
                print("-" * 50)
                print(rec)
                print()
        
        print("\n" + "=" * 50)
        print("🏁 Defense Analysis Complete!")
        print("=" * 50)
        
        return {
            "status": "success",
            "messages": result["messages"],
            "recommendations": recommendations
        }
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "messages": []
        }

if __name__ == "__main__":
    # Read logs from the test lab
    with open("app_logs/app.log", "r") as f:
        security_logs = f.read()
        
    # Run defensive analysis
    result = main(security_logs)
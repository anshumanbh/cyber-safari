from typing import List, Dict, Any
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from tools.defense_tools import analyze_logs, identify_security_controls, generate_recommendations
from tools.common import log_progress

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
        model=llm_with_system
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
    with open("app_logs/app.log", "r") as f:  # Updated path to account for new location
        security_logs = f.read()
        
    # Run defensive analysis
    result = main(security_logs) 
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import json
from .security_kb_tool import init_security_tool
from .common import log_progress

@tool
def analyze_logs(log_content: str) -> Dict[str, Any]:
    """
    Analyzes application logs to identify potential security attacks.
    
    Args:
        log_content: String containing application logs
        
    Returns:
        Dictionary containing identified attack patterns and details
    """
    log_progress("Analyzing application logs for attack patterns...", prefix="🛡️")
    
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
        
        log_progress(f"Identified {analysis['attack_type']} attack targeting {analysis['target']}", prefix="🛡️")
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
    log_progress(f"Identifying security controls for {attack_analysis['attack_type']} attack...", prefix="🛡️")
    
    try:

        security_kb = init_security_tool()
        if not security_kb:
            raise ValueError("Failed to initialize security knowledge base")
        
        query = f"""
        How to protect against {attack_analysis['attack_type']} attacks 
        targeting {attack_analysis['target']} where {attack_analysis['vulnerability']} 
        is being exploited?
        """

        log_progress(f"Query: {query}")
        print("=" * 50)
        
        # Query knowledge base
        controls = security_kb.invoke({"query": query})
        
        if 'results' not in controls:
            raise ValueError("Security controls query returned invalid response")
            
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
    log_progress("Generating security control recommendations...", prefix="🛡️")
    
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
        
        log_progress(f"Generating recommendations for {security_info['attack_analysis']['attack_type']} attack...", prefix="🛡️")
        log_progress(f"Recommendations Prompt: {recommendations_prompt}")
        print("=" * 50)
        response = llm.invoke(recommendations_prompt)
        recommendations = json.loads(response.content)
        
        log_progress(f"Generated Recommendations: {recommendations}")
        print("=" * 50)
        
        return recommendations
        
    except Exception as e:
        log_progress(f"❌ Error generating recommendations: {str(e)}")
        return {"error": str(e)}
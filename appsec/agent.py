from textwrap import dedent
from typing import Dict, Any, Literal

from autogen import ConversableAgent


MANAGER_AGENT_NAME = "Manager_Agent"
REVIEWER_AGENT_NAME = "Code_Reviewer_Agent"
VULNERABILITY_EXPLOITER_AGENT_NAME = "Vulnerability_Exploiter_Agent"
MITIGATION_EXPERT_AGENT_NAME = "Mitigation_Expert_Agent"

AgentName = Literal[
    "Manager_Agent",
    "Code_Reviewer_Agent",
    "Vulnerability_Exploiter_Agent",
    "Mitigation_Expert_Agent"
]

REVIEWER_AGENT_DESCRIPTION = "Assigned with the task of reviewing code and pinpointing all critical vulnerabilities."
EXPLOITER_AGENT_DESCRIPTION = "Assigned with the task of exploiting vulnerability findings from the code review process."
MITIGATION_AGENT_DESCRIPTION = dedent("""
You are assigned with the task of mitigating the findings from the discovered vulnerabilities and exploits, 
suggesting fixes and the best tools for the job, including native libraries and code changes where relevant.
Provide security improvement suggestions for specific lines of code that should be improved. 
When suggesting changes for one file, you should not suggest the addition or moving of code to another file.
""")

HumanInputMode = Literal["ALWAYS", "NEVER", "TERMINATE"]


class AgentFactory:

    def __init__(self, llm_config: Dict[str, Any]):
        self.llm_config = llm_config

    def create_agent(self, name: AgentName, description: str = None, system_message: str = None, human_input_mode: HumanInputMode = "NEVER"):
        if system_message:
            return ConversableAgent(
                name=name,
                system_message=system_message,
                llm_config=self.llm_config,
                human_input_mode=human_input_mode,
                description=description
            )
        else:
            return ConversableAgent(
                name=name,
                llm_config=self.llm_config,
                human_input_mode=human_input_mode,
                description=description
            )
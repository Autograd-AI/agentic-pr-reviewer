import re
import json
import autogen

from appsec.exceptions import (
    LLMProviderAPIKeyNotSetException,
)

from dynaconf import Dynaconf
from dotenv import load_dotenv
from github import PullRequest, Commit, PullRequestReview


from langchain.output_parsers import PydanticOutputParser
from langchain.output_parsers.fix import OutputFixingParser

from appsec.schemas import CodeSuggestions, CodeSuggestion

from appsec.utils import (
    extract_hunks,
    get_llm_settings_config,
    get_llm,
    has_set_llm_provider_api_key,
)

from appsec.clients.github import get_client as get_github_client

from appsec.agent import (
    REVIEWER_AGENT_NAME,
    MANAGER_AGENT_NAME,
    MITIGATION_EXPERT_AGENT_NAME,
    VULNERABILITY_EXPLOITER_AGENT_NAME,
)
from appsec.agent import AgentFactory

from .agent import (
    REVIEWER_AGENT_DESCRIPTION,
    MITIGATION_AGENT_DESCRIPTION,
    EXPLOITER_AGENT_DESCRIPTION
)


def build_pull_request_file_context(repo_name: str, pull_request_number: int) -> str:
    client = get_github_client()
    repo_object = client.get_repo(
        repo_name
    )
    pull_request = repo_object.get_pull(pull_request_number)

    files = pull_request.get_files()

    context = (
        'Here are the code changes:\n'
    )
    for file in files:
        hunks = extract_hunks(file.patch)

        patch = ""
        for hunk_header, old_code, new_code in hunks:
            formatted_hunk = "\n".join([hunk_header, '__old_code__', old_code, '__new_code__', new_code])
            patch = f'{patch}\n\n{formatted_hunk}'

        context = (
            f'{context}<file_name>{file.filename}</file_name><patch>{patch}</patch>\n'
        )

    return context


def parse_code_suggestions(content: str) -> CodeSuggestions:
    llm = get_llm()
    parser = OutputFixingParser.from_llm(
        llm=llm,
        parser=PydanticOutputParser(pydantic_object=CodeSuggestions)
    )
    parsed_result: CodeSuggestions = parser.parse(
        content
    )
    return parsed_result


def create_inline_suggestion_review(suggestion: CodeSuggestion, pull_request: PullRequest, head_commit: Commit.Commit) -> PullRequestReview.PullRequestReview:
    print(("suggestion", suggestion))
    return pull_request.create_review(
        commit=head_commit,
        event="COMMENT",
        body=suggestion.summary,
        comments=[{
            "path": suggestion.filename,
            "line": suggestion.line_number_end,
            "start_line": suggestion.line_number_start,
            "start_side": "RIGHT",
            "body": f"{suggestion.summary}\n```suggestion\n{suggestion.suggested_code}\n```"
        }]
    )


async def execute_agents(repo: str, to_event: str, from_event: str = None):
    prompt_templates = Dynaconf(
        envvar_prefix=False,
        settings_files=[
            'appsec/prompts/code_suggestions.toml',
            'appsec/prompts/manager_agent.toml',
        ],
    )
    print(("prompt_templates", prompt_templates, dir(prompt_templates)))

    code_suggestion_prompt = prompt_templates.code_suggestion_prompt.system
    print(("code_suggestion_prompt", code_suggestion_prompt))

    parser = PydanticOutputParser(pydantic_object=CodeSuggestions)

    code_suggestion_prompt = code_suggestion_prompt.format(
        formatting_instructions=parser.get_format_instructions()
    )
    print("code_suggestion_prompt.2")
    print(code_suggestion_prompt)

    manager_agent_system_message = prompt_templates.manager_agent.system
    print(("manager_agent_system_message", manager_agent_system_message))

    if to_event.isdigit():
        pull_request_number = int(to_event)
    else:
        raise Exception("Only single pull request reviews are currently supported")

    context = build_pull_request_file_context(
        repo_name=repo,
        pull_request_number=pull_request_number
    )

    llm_config = get_llm_settings_config()

    agent_factory = AgentFactory(
        llm_config=llm_config
    )
    manager_agent = agent_factory.create_agent(
        name=MANAGER_AGENT_NAME,
        system_message=manager_agent_system_message,
        human_input_mode="NEVER"
    )
    reviewer_agent = agent_factory.create_agent(
        name=REVIEWER_AGENT_NAME,
        description=REVIEWER_AGENT_DESCRIPTION,
        system_message=code_suggestion_prompt
    )
    exploiter_agent = agent_factory.create_agent(
        name=VULNERABILITY_EXPLOITER_AGENT_NAME,
        description=EXPLOITER_AGENT_DESCRIPTION,
        system_message=code_suggestion_prompt,
    )
    migration_expert_agent = agent_factory.create_agent(
        name=MITIGATION_EXPERT_AGENT_NAME,
        description=MITIGATION_AGENT_DESCRIPTION,
        system_message=code_suggestion_prompt
    )

    logging_session_id = autogen.runtime_logging.start(config={"dbname": "logs.db"})

    chat_results = manager_agent.initiate_chats([
        {
            "recipient": reviewer_agent,
            "message": context,
            "max_turns": 2,
            "summary_method": "last_msg",
            "verbose": True,
        },
        {
            "recipient": exploiter_agent,
            "message": context,
            "max_turns": 1,
            "summary_method": "last_msg",
            "verbose": True,
        },
        {
            "recipient": migration_expert_agent,
            "message": context,
            "max_turns": 1,
            "summary_method": "last_msg",
            "verbose": True,
        }
    ])
    autogen.runtime_logging.stop()
    print(("chat_results", chat_results))

    mitigation_expert_result = chat_results[-1].chat_history[-1]
    print(("mitigation_expert_result", mitigation_expert_result))

    content = mitigation_expert_result.get('content')

    client = get_github_client()
    repo_object = client.get_repo(repo)
    pull_request = repo_object.get_pull(pull_request_number)
    head_commit = repo_object.get_commit(pull_request.head.sha)

    parsed_result = parse_code_suggestions(content)
    print("parsed_result.suggestions")
    print(parsed_result.suggestions)
    for suggestion in parsed_result.suggestions:
        inline_review = create_inline_suggestion_review(
            suggestion=suggestion,
            pull_request=pull_request,
            head_commit=head_commit
        )
        print(("inline_review", inline_review))



async def main(
    repo: str,
    to_event: str,
    from_event: str = None
):
    load_dotenv()
    if not has_set_llm_provider_api_key():
        raise LLMProviderAPIKeyNotSetException()

    await execute_agents(repo, to_event, from_event)

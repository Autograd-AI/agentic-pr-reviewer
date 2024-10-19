from typing import List
from pydantic import BaseModel, Field


class CodeSuggestion(BaseModel):
    filename: str = Field(description="Complete path of the relevant file for which code is to be changed. "
                                      "You must include the entire URL path as provided in the context. "
                                      "Do not attempt to shorten it in any way. "
                                      "Return the original file_name contained with <file_name></file_name>, verbatim."
                                      "Do not include the surrounding <file_name> tags.")
    language: str = Field(description="Relevant language of the code change")
    line_number_start: int = Field(
        description="The relevant line number, from a '__new_code__' section, where the updated suggested code starts (inclusive). Should reflect hunk line numbers.")
    line_number_end: int = Field(
        description="The relevant line number, from a '__new_code__' section, where the suggestion ends. Should be derived from the hunk line numbers. This must proceed the start line must proceed the 'line_number_start' value.")
    previous_code: str = Field(
        description="A short code snippet representing for which a change or improvement is suggested. "
                    "Only include the suggested code and immediately proceeding and preceding unchanged lines of code. "
                    "Do not include code lines for which no specific change is suggested."
                    "Code must reflect the actual code (**verbatim**) provided in the PR patch.")
    suggested_code: str = Field(
        description="A refined code snippet that replaces the 'previous_code' snippet after implemeting the suggestions. "
                    "Only ever output code suggestions for the specific lines where a change is required. "
                    "Do not include existing code in your suggested output for which no change is required, even if some existing code is adjacent to your code suggestion lines. "
                    "Do not suggest rewriting lines of code or changing the order of imports unless there is a very compelling reason. "
                    "This must reflect the actual code provided in the PR patch. "
                    "You should only provide suggested changes for '__new_code__' hunks. You should never make suggested changes for '__old_code__' hunks. "
                    "'__olc_code__' hunks are for reference purposes only.")
    summary: str = Field(
        description="Succinct explanation for the suggested code change. Encapsulate any references to code or file names with starting and ending backticks (i.e., '`')"
    )


class CodeSuggestions(BaseModel):
    suggestions: List[CodeSuggestion]

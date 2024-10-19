import os

from github import Github
from github import Auth


def get_client() -> Github:
    return Github(auth=Auth.Token(os.getenv('GITHUB_API_TOKEN')))
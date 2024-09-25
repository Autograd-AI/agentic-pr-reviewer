from textwrap import dedent


class InvalidateCredentialsException(Exception):

    def __str__(self):
        return dedent(
            """
            The API token you provided is invalid. 
            Did you or a member of your team regenerate your team's API token? 
            Go to the following link to obtain a valid token: https://app.autograd.ai/integrations/api
            """
        )


class APITokenNotSetException(Exception):
    def __str__(self):
        return dedent(
            """
            An AUTOGRAD_API_TOKEN environment variable has not been set.  
            Environment variables can be set at an organization or repo level. 
            More information is available here: https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables
            """
        )


class BadRequestException(Exception):
    pass


class ServerErrorException(Exception):

    def __str__(self):
        return dedent(
            "Something went wrong. Please contact support: developers@autograd.ai"
        )

class SeverityActionFailureException(Exception):
    pass

import os
import aiohttp

from .urls import CREATE_RUN_ENDPOINT

from .exceptions import (
    InvalidateCredentialsException,
    BadRequestException,
    ServerErrorException,
    APITokenNotSetException,
    SeverityActionFailureException
)


async def create_run(session, repo: str, to_event: str, from_event: str = None):
    async with session.post(url=CREATE_RUN_ENDPOINT, json={
        'repo': repo,
        'to_event': to_event,
        'from_event': from_event
    }) as response:
        action_failure_reviews = []
        if response.status >= 400:
            try:
                error_detail = await response.json()  # Get error details from JSON response
            except aiohttp.ContentTypeError as ex:
                # Handle cases where the response isn't JSON
                error_detail = await response.text()

            if response.status in [400, 404]:
                raise BadRequestException(error_detail)
            elif response.status == 403:
                raise InvalidateCredentialsException(error_detail)
            elif response.status == 500:
                raise ServerErrorException()
            else:
                # raise a generic error
                response.raise_for_status()

        res = await response.json()
        reviews = res.get("reviews", [])
        for review in reviews:
            if review.get("severity_failure"):
                action_failure_reviews.append(review)

        if action_failure_reviews:
            exception_detail = '\n'.join([f"Reason: {o.reason}, Severity: {o.severity_failure}" for o in action_failure_reviews])
            raise SeverityActionFailureException(
                f"The following reviews have a failure severity level: {exception_detail}"
            )


async def main(
    repo: str,
    to_event: str,
    from_event: str = None
):
    api_token = os.getenv('AUTOGRAD_API_TOKEN')
    if not api_token:
        raise APITokenNotSetException()

    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        await create_run(session, repo, to_event, from_event)

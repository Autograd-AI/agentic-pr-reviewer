import os
import aiohttp

from .urls import CREATE_RUN_ENDPOINT


async def create_run(session, repo: str, to_event: str, from_event: str = None):
    async with session.post(url=CREATE_RUN_ENDPOINT, json={
        'repo': repo,
        'to_event': to_event,
        'from_event': from_event
    }) as response:
        return await response.json()


async def main(
    repo: str,
    to_event: str,
    from_event: str = None
):
    api_token = os.getenv('AUTOGRAD_API_TOKEN')
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            result = await create_run(session, repo, to_event, from_event)
    except aiohttp.ClientError as ex:
        print(str(ex))



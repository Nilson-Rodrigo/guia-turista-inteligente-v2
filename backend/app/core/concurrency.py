import asyncio


active_requests: set[str] = set()
request_lock = asyncio.Lock()

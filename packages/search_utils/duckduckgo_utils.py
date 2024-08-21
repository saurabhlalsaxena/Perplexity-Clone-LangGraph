#duckduckgo_utils.py
import asyncio

from duckduckgo_search import AsyncDDGS

async def aget_results(word):
    results = await AsyncDDGS(proxy=None).atext(word, max_results=2)
    return results

async def search(queries):
    words = queries
    tasks = [aget_results(w) for w in words]
    results = await asyncio.gather(*tasks)
    return results
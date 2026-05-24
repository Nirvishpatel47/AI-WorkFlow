import asyncio
from Security.get_secretes import load_env_from_secret
import redis.asyncio as redis


REDIS_URL = load_env_from_secret("REDIS_HOST")


async def test_redis():

    try:
        r = redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

        await r.set("test_key", "hello")

        value = await r.get("test_key")

        print("Redis Connected")
        print("Value:", value)

    except Exception as e:
        print("Redis Failed")
        print(e)


asyncio.run(test_redis())
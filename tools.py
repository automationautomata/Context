import logging
import sys


def pipeline(middlewares: list):
    async def wrapper(*args, **kwargs):
        for check, handler in middlewares:
            if check(*args, **kwargs):
                await handler(*args, **kwargs)

    return wrapper


def counter(func, num, action_func=None):
    cnt = 0

    async def wrapper(*args, **kwargs):
        nonlocal cnt, num
        cnt += 1
        if cnt >= num:
            return await action_func(*args, **kwargs) if action_func else None
        return await func(*args, **kwargs)

    return wrapper


def catch_exception(func):
    async def wrapper(*args):
        try:
            return await func(*args)
        except BaseException:
            logging.warning(msg=f"{func.__qualname__} {sys.exc_info()[:2]}")

    return wrapper

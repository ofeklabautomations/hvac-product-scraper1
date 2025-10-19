import urllib.robotparser as urobot
from urllib.parse import urljoin, urlparse
from functools import lru_cache

@lru_cache(maxsize=128)
def get_robot_parser(base_url: str):
    rp = urobot.RobotFileParser()
    root = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
    rp.set_url(urljoin(root, "/robots.txt"))
    try:
        rp.read()
    except Exception:
        pass
    return rp

def allowed(user_agent: str, base_url: str, url: str) -> bool:
    rp = get_robot_parser(base_url)
    try:
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True  # if robots can't be read, default to allow (you can make this stricter)


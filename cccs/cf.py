import hashlib
import random
import string
from time import time
from urllib import parse

from cccs.network import get


class CodeforcesContest:
    def __init__(self, id, key, secret) -> None:
        self.id = id
        self.key = key
        self.secret = secret

        self.standings = self.api("contest.standings", **{"from": 1, "count": 1})

    def api(self, method: str, **kwargs):
        assert method.startswith("contest")
        params = {
            "apiKey": self.key,
            "time": int(time()),
            "contestId": self.id,
            **kwargs,
        }
        params = dict(sorted(params.items()))
        rand = "".join(random.choices(string.digits + string.ascii_lowercase, k=6))
        raw = f"{rand}/{method}?{parse.urlencode(params)}#{self.secret}"
        params["apiSig"] = rand + hashlib.sha512(raw.encode()).hexdigest()
        url = f"https://codeforces.com/api/{method}?{parse.urlencode(params)}"
        return get(url).json()["result"]

    @property
    def contest(self) -> dict:
        return self.standings["contest"]

    @property
    def problems(self) -> dict:
        return self.standings["problems"]

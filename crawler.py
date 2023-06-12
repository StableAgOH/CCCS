import json
import time

from bs4 import BeautifulSoup

from cccs.network import get, post

gym_id = json.load(open("config.json", "r", encoding="UTF-8"))["gym_id"]

DOMAIN = "https://mirror.codeforces.com/"


resp = get(DOMAIN + f"gym/{gym_id}/standings")
pages = int(
    BeautifulSoup(resp.content, "lxml")
    .find("div", {"class": "custom-links-pagination"})
    .find_all("nobr")[-1]
    .find("span")
    .attrs["pageindex"]
)

teams, submissions = [], []
for page in range(1, pages + 1):
    time.sleep(1)
    standings = get(DOMAIN + f"gym/{gym_id}/standings/page/{page}")
    standings = BeautifulSoup(standings.content, "lxml")

    table = standings.find("table", {"class": "standings"})
    for tr in table.find_all("tr"):
        team_id = tr.attrs.get("participantid")
        if not team_id:
            continue
        team_name = tr.find_all("td")[1].text.strip()
        teams.append([team_id, team_name])
        print(tr.find_all("td")[0].text.strip(), team_name)

        time.sleep(1)
        team_submissions = post(DOMAIN + "data/standings", {"participantId": team_id})
        team_submissions = team_submissions.json()
        for ts in team_submissions:
            problem = BeautifulSoup(ts["problem"], "lxml").text
            contest_time = ts["contestTime"]
            result = BeautifulSoup(ts["verdict"], "lxml").text
            submissions.append([team_id, problem, contest_time, result])

json.dump(teams, open("teams.json", "w", encoding="UTF-8"), ensure_ascii=False)
submissions.sort(key=lambda x: x[2])
json.dump(
    submissions,
    open("submissions.json", "w", encoding="UTF-8"),
    ensure_ascii=False,
)

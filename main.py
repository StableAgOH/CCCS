import asyncio
import datetime
import json
import random
import re
import threading
import time
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, StreamingResponse

from src.cf import CodeforcesContest
from src.colors import colors
from src.contest import Contest

config = json.load(open("config.json", "r", encoding="UTF-8"))
scoreboard_freeze_duration = timedelta(hours=config["freeze_hours"])

ghost_teams = json.load(open("teams.json", "r", encoding="UTF-8"))
ghost_submissions = json.load(open("submissions.json", "r", encoding="UTF-8"))

cf = CodeforcesContest(config["mashup_id"], config["key"], config["secret"])
start_time = datetime.fromtimestamp(cf.contest["startTimeSeconds"])
duration = timedelta(seconds=cf.contest["durationSeconds"])
end_time = start_time + duration
frozen_time = end_time - scoreboard_freeze_duration

# Create contest
contest = Contest(
    id=config["mashup_id"],
    name=cf.contest["name"],
    start_time=start_time,
    duration=duration,
    scoreboard_freeze_duration=scoreboard_freeze_duration,
    penalty_time=20,
)

# Add judgement types
contest.update_judgement_type(id="AC", name="Accepted", penalty=False, solved=True)
contest.update_judgement_type(id="RE", name="Rejected", penalty=True, solved=False)

# Add languages
contest.update_language(id="unk", name="Unknown")
contest.update_language(id="c", name="C")
contest.update_language(id="c++", name="C++")
contest.update_language(id="java", name="Java")
contest.update_language(id="python", name="Python")
contest.update_language(id="other", name="Other")


def get_lang(lang: str):
    if lang.find("gcc") != -1:
        return "c"
    if lang.find("++") != -1:
        return "c++"
    if lang.find("java ") != -1:
        return "java"
    if lang.find("py") != -1:
        return "python"
    return "other"


# Add problems
for i, problem in enumerate(cf.problems):
    color = colors[i] if i < len(colors) else f"#{hex(random.randint(0, 16777215))[2:]}"
    contest.update_problem(
        id=problem["index"],
        label=problem["index"],
        name=problem["name"],
        ordinal=i,
        rgb=color,
        time_limit=1,
        test_data_count=10,
    )

# Add groups
contest.update_group(id="ghost", name="ghost")
contest.update_group(id="contestant", name="contestant")

# Add ghost teams
for gt in ghost_teams:
    contest.add_team_if_not_exists(id=f"Ghost@{gt[0]}", name=gt[1], group_ids=["ghost"])


def get_event():
    p = 0
    done = set()
    while True:
        now = datetime.now()
        if now > end_time:
            contest.update_state(
                started=start_time,
                frozen=frozen_time,
                ended=end_time,
                thawed=None,
                finalized=None,
            )
        elif now > frozen_time:
            contest.update_state(
                started=start_time,
                frozen=frozen_time,
                ended=None,
                thawed=None,
                finalized=None,
            )
        elif now > start_time:
            contest.update_state(
                started=start_time,
                frozen=None,
                ended=None,
                thawed=None,
                finalized=None,
            )
        while p < len(ghost_submissions):
            gs = ghost_submissions[p]
            h, m, s = map(int, re.match(r"(\d+)\:(\d+)\:(\d+)", gs[2]).groups())
            td = timedelta(hours=h, minutes=m, seconds=s)
            submit_time = start_time + td
            if submit_time > now:
                break
            contest.update_submission(
                id=str(p + 1),
                language_id="unk",
                problem_id=gs[1],
                team_id=f"Ghost@{gs[0]}",
                time=submit_time,
                contest_time=td,
            )
            contest.update_judgement(
                id=str(p + 1),
                submission_id=str(p + 1),
                judgement_type_id="AC" if gs[3] == "Accepted" else "RE",
                start_time=submit_time,
                start_contest_time=td,
                end_time=submit_time,
                end_contest_time=td,
            )
            p += 1
        status = cf.api("contest.status")
        status = filter(
            lambda s: s["author"]["participantType"] == "CONTESTANT"
            and str(s["id"]) not in done,
            status,
        )
        for s in status:
            sid = str(s["id"])
            verdict = s["verdict"]
            lang_id = get_lang(s["programmingLanguage"].lower())
            submit_time = datetime.fromtimestamp(s["creationTimeSeconds"])
            contest_time = submit_time - start_time
            team_id = s["author"].get("teamId")
            if team_id:
                team_id = f"Team@{team_id}"
                team_name = s["author"]["teamName"]
            else:
                team_name = s["author"]["members"][0]["handle"]
                team_id = f"User@{team_name}"
            contest.add_team_if_not_exists(
                id=team_id, name=team_name, group_ids=["contestant"]
            )

            contest.update_submission(
                id=sid,
                language_id=lang_id,
                problem_id=s["problem"]["index"],
                team_id=team_id,
                time=submit_time,
                contest_time=contest_time,
            )
            if verdict == "OK":
                contest.update_judgement(
                    id=sid,
                    submission_id=sid,
                    judgement_type_id="AC",
                    start_time=submit_time,
                    start_contest_time=contest_time,
                    end_time=submit_time,
                    end_contest_time=contest_time,
                )
                done.add(sid)
            elif verdict == "TESTING":
                contest.update_judgement(
                    id=sid,
                    submission_id=sid,
                    judgement_type_id=None,
                    start_time=submit_time,
                    start_contest_time=contest_time,
                    end_time=None,
                    end_contest_time=None,
                )
            else:
                contest.update_judgement(
                    id=sid,
                    submission_id=sid,
                    judgement_type_id="RE",
                    start_time=submit_time,
                    start_contest_time=contest_time,
                    end_time=submit_time,
                    end_contest_time=contest_time,
                )
                done.add(sid)

        if now > end_time:
            break
        time.sleep(3)


event_creator = threading.Thread(target=get_event)
event_creator.daemon = True
event_creator.start()


app = FastAPI()


async def event_feed(req: Request):
    p, c = 0, 0
    while True:
        if await req.is_disconnected():
            break
        if p < len(contest.events):
            c = 0
            yield contest.events[p].jsonstr() + "\n"
            p += 1
        else:
            await asyncio.sleep(5)
            c += 1
            if c == 20:
                yield "\n"
                c = 0


@app.get(f"/api/contests/{config['mashup_id']}/event-feed")
async def api_contests_event_feed(req: Request, stream: bool = True):
    if stream:
        return StreamingResponse(event_feed(req))
    else:
        return PlainTextResponse("\n".join(map(lambda e: e.jsonstr(), contest.events)))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5353)

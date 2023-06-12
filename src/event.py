import json
from dataclasses import dataclass
from datetime import datetime, timedelta


def reltime(td: timedelta):
    hours, remainder = divmod(int(td.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}"


def tzdatetime(dt: datetime):
    return dt.astimezone().isoformat(timespec="milliseconds")


@dataclass
class EventData:
    def jsonobj(self) -> str:
        return self.__dict__


@dataclass
class Event:
    id: str
    type: str
    data: EventData

    def jsonstr(self):
        obj = self.__dict__.copy()
        obj["data"] = self.data.jsonobj()
        return json.dumps(obj)


@dataclass
class ContestEventData(EventData):
    id: str
    name: str
    start_time: datetime
    duration: timedelta
    scoreboard_freeze_duration: timedelta
    scoreboard_type = "pass-fail"
    penalty_time: int

    def jsonobj(self):
        obj = self.__dict__.copy()
        obj["start_time"] = tzdatetime(self.start_time)
        obj["duration"] = reltime(self.duration)
        obj["scoreboard_freeze_duration"] = reltime(self.scoreboard_freeze_duration)
        return obj


class ContestEvent(Event):
    def __init__(self, **kwargs) -> None:
        super().__init__(None, "contests", ContestEventData(**kwargs))


@dataclass
class JudgementTypeEventData(EventData):
    id: str
    name: str
    penalty: bool
    solved: bool


class JudgementTypeEvent(Event):
    def __init__(self, mid: str, **kwargs) -> None:
        super().__init__(mid, "judgement-types", JudgementTypeEventData(**kwargs))


@dataclass
class LanguageEventData(EventData):
    id: str
    name: str


class LanguageEvent(Event):
    def __init__(self, mid: str, **kwargs) -> None:
        super().__init__(mid, "languages", LanguageEventData(**kwargs))


@dataclass
class ProblemEventData(EventData):
    id: str
    label: str
    name: str
    ordinal: int
    rgb: str
    time_limit: int
    test_data_count: int


class ProblemEvent(Event):
    def __init__(self, mid: str, **kwargs) -> None:
        super().__init__(mid, "problems", ProblemEventData(**kwargs))


@dataclass
class GroupEventData(EventData):
    id: str
    name: str


class GroupEvent(Event):
    def __init__(self, mid: str, **kwargs) -> None:
        super().__init__(mid, "groups", GroupEventData(**kwargs))


@dataclass
class TeamEventData(EventData):
    id: str
    name: str
    group_ids: list[str]


class TeamEvent(Event):
    def __init__(self, mid: str, **kwargs) -> None:
        super().__init__(mid, "teams", TeamEventData(**kwargs))


@dataclass
class StateEventData(EventData):
    started: datetime
    frozen: datetime
    ended: datetime
    thawed: datetime
    finalized: datetime

    def jsonobj(self) -> str:
        obj = self.__dict__.copy()
        if obj["started"]:
            obj["started"] = tzdatetime(self.started)
        if obj["frozen"]:
            obj["frozen"] = tzdatetime(self.frozen)
        if obj["ended"]:
            obj["ended"] = tzdatetime(self.ended)
        if obj["thawed"]:
            obj["thawed"] = tzdatetime(self.thawed)
        if obj["finalized"]:
            obj["finalized"] = tzdatetime(self.finalized)
        return obj


class StateEvent(Event):
    def __init__(self, **kwargs) -> None:
        super().__init__(None, "state", StateEventData(**kwargs))


@dataclass
class SubmissionEventData(EventData):
    id: str
    language_id: str
    problem_id: str
    team_id: str
    time: datetime
    contest_time: timedelta

    def jsonobj(self) -> str:
        obj = self.__dict__.copy()
        obj["time"] = tzdatetime(self.time)
        obj["contest_time"] = reltime(self.contest_time)
        return obj


class SubmissionEvent(Event):
    def __init__(self, mid: str, **kwargs) -> None:
        super().__init__(mid, "submissions", SubmissionEventData(**kwargs))


@dataclass
class JudgementEventData(EventData):
    id: str
    submission_id: str
    judgement_type_id: str
    start_time: datetime
    start_contest_time: timedelta
    end_time: datetime
    end_contest_time: timedelta

    def jsonobj(self) -> str:
        obj = self.__dict__.copy()
        obj["start_time"] = tzdatetime(self.start_time)
        obj["start_contest_time"] = reltime(self.start_contest_time)
        if obj["end_time"]:
            obj["end_time"] = tzdatetime(self.end_time)
        if obj["end_contest_time"]:
            obj["end_contest_time"] = reltime(self.end_contest_time)
        return obj


class JudgementEvent(Event):
    def __init__(self, mid: str, **kwargs) -> None:
        super().__init__(mid, "judgements", JudgementEventData(**kwargs))

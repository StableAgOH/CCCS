from cccs.event import Event, ContestEvent, JudgementEvent, JudgementTypeEvent, LanguageEvent, ProblemEvent, GroupEvent, TeamEvent, StateEvent, SubmissionEvent


class Contest:
    def __init__(self, **kwargs):
        self.events: list[Event] = []
        self.tid_set: set[str] = set()
        self.lang_dict: dict[str, str] = {}
        self.sid_cnt, self.jid_cnt, self.lid_cnt = 1, 1, 1

        self.update_event(ContestEvent(**kwargs))

    def update_event(self, event: Event):
        self.events.append(event)

    def update_judgement_type(self, **kwargs):
        self.update_event(JudgementTypeEvent(kwargs["id"], **kwargs))

    def update_language(self, **kwargs):
        self.update_event(LanguageEvent(kwargs["id"], **kwargs))

    def ensure_language(self, name: str):
        lid = self.lang_dict.get(name)
        if lid:
            return lid

        new_id = str(self.lid_cnt)
        self.lang_dict[name] = new_id
        self.update_language(id=new_id, name=name)
        self.lid_cnt += 1
        return new_id

    def update_problem(self, **kwargs):
        self.update_event(ProblemEvent(kwargs["id"], **kwargs))

    def update_group(self, **kwargs):
        self.update_event(GroupEvent(kwargs["id"], **kwargs))

    def add_team_if_not_exists(self, **kwargs):
        _id = kwargs["id"]
        if _id not in self.tid_set:
            self.tid_set.add(_id)
            self.update_event(TeamEvent(_id, **kwargs))

    def update_state(self, **kwargs):
        self.update_event(StateEvent(**kwargs))

    def update_submission(self, **kwargs):
        self.update_event(SubmissionEvent(kwargs["id"], **kwargs))

    def update_judgement(self, **kwargs):
        self.update_event(JudgementEvent(kwargs["id"], **kwargs))

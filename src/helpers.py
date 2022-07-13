from typing import List, Any
import random
from pytwitter import StreamApi
from pytwitter.models import Response
from data import RULES
from emoji import EMOJI_DATA


def del_rules(*id: int) -> dict:
    """
    Generate a dict to delete rules
    """
    return {"delete": {"ids": [str(id) for id in id]}}


def del_all(stream: StreamApi):
    """
    Delete all rules from the stream
    """
    rules = stream.get_rules()
    if isinstance(rules, Response):
        to_be_deleted: List[int] = []
        if rules.data:
            to_be_deleted = [int(rule.id) for rule in rules.data]  # type: ignore

        if len(to_be_deleted) > 0:
            stream.manage_rules(del_rules(*to_be_deleted))

        return to_be_deleted


def reset_rules(stream: StreamApi):
    """
    Delete all rules and add the default ones
    """
    del_all(stream)
    stream.manage_rules(rules=RULES)
    print(stream.get_rules())


def is_valid_text(text: str):
    for char in text:
        if char and char.isdigit() and char not in EMOJI_DATA:
            return False
    return True


def shuffle_list(list_: List[Any]):
    random.Random(timestamp).shuffle(list_)
    return list_

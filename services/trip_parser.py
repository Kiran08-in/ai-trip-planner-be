import json
import re

from pydantic import ValidationError

from schema import TripRequest
from services.ai import ask_ai

SYSTEM_PROMPT = (
    "You extract trip details from a sentence. "
    "Reply with ONLY a JSON object with keys: "
    "destination (string, or null if no place is named), "
    "days (integer), "
    "budget (integer, total in Indian rupees, or null if no number is given). "
    "Never guess. Use null for anything the sentence does not state. "
    "No other text."
)


class NeedMoreInfo(Exception):
    pass


class ParseFailed(Exception):
    pass


def extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match is None:
        raise ValueError("no JSON object found")
    return json.loads(match.group(0))


async def parse_trip(sentence):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": sentence},
    ]
    problem = ""

    for _ in range(2):
        answer = await ask_ai(messages)
        try:
            data = extract_json(answer)
        except ValueError as e:
            problem = str(e)
        else:
            destination = data.get("destination")
            if not isinstance(destination, str) or not destination.strip():
                raise NeedMoreInfo("Please tell me which city you want to visit.")
            if data.get("budget") is None:
                raise NeedMoreInfo("Please tell me your budget as a number, for example 15000 rupees.")
            days = data.get("days")
            if isinstance(days, int) and not 1 <= days <= 7:
                raise NeedMoreInfo("TripBanao plans 1 to 7 days. Please choose fewer days.")
            try:
                return TripRequest(**data)
            except ValidationError as e:
                problem = str(e)

        messages.append({"role": "assistant", "content": answer})
        messages.append({
            "role": "user",
            "content": f"That was not valid: {problem}. Reply again with ONLY the JSON object.",
        })

    raise ParseFailed("I could not understand that. Please use the form instead.")
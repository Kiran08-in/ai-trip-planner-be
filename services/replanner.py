from pydantic import ValidationError

from schema import PlanOptions
from services.ai import ask_ai
from services.trip_parser import extract_json

SYSTEM_PROMPT = (
    "You turn a traveler's request into changes for a trip plan. "
    "Reply with ONLY a JSON object with these keys: "
    "places_per_day (integer 1 to 4, or null), "
    "avoid_types (list using only: temple, beach, park, viewpoint, attraction), "
    "indoor_only (true or false), "
    "max_hop_km (number of km between stops, or null), "
    "reason (one short sentence for the traveler). "
    "Use null, an empty list or false for anything the request does not ask for. "
    "For 'less walking' use places_per_day 2 and max_hop_km 3. "
    "If the traveler wants it cheaper, use places_per_day 2 and say in the reason "
    "that only entry fees can go down. "
    "Never guess. No other text."
)


class ReplanFailed(Exception):
    pass


async def understand_request(text):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    problem = ""

    for _ in range(2):
        answer = await ask_ai(messages)
        try:
            data = extract_json(answer)
        except ValueError as e:
            problem = str(e)
        else:
            reason = str(data.pop("reason", "") or "")[:200]
            values = {k: v for k, v in data.items() if v is not None}
            try:
                options = PlanOptions(**values)
            except ValidationError as e:
                problem = str(e)
            else:
                if options == PlanOptions():
                    raise ReplanFailed(
                        "I could not find a change to make. Try: less walking, no temples, or only indoor places."
                    )
                return options, reason

        messages.append({"role": "assistant", "content": answer})
        messages.append({
            "role": "user",
            "content": f"That was not valid: {problem}. Reply again with ONLY the JSON object.",
        })

    raise ReplanFailed("I could not understand that. Please try again in other words.")
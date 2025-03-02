import asyncio
import json
from ector import extract

user_input_en = """
Hi, I'm looking for a laptop with a high-resolution screen and
fast processor at 150 usd max.
I also need a wireless mouse. Do you have any external monitors. i want also a green
Android IPhone.
And for all of that, i have a budget of 200 eur.
"""

user_input_fr = "je veux un iPhone noire et aussi des Jordans. mais j'ai un budget de 300 dollars."

async def main():
    print(user_input_en)
    result = await extract(user_input_en, "en")
    print(json.dumps(result, indent=4))

    print("-" * 100)
    print(user_input_fr)
    result = await extract(user_input_fr, "fr")
    print(json.dumps(result, indent=4))

asyncio.run(main())

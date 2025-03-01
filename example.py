import asyncio
import json
from ector import extract

user_input = """
Hi, I'm looking for a laptop with a high-resolution screen and
fast processor at 150 usd max.
I also need a wireless mouse. Do you have any external monitors. i want also a green
Android IPhone.
And for all of that, i have a budget of 200 eur.
"""

async def main():
    print(user_input)
    result = await extract(user_input)
    print(json.dumps(result, indent=4))

asyncio.run(main())

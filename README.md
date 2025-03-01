## ECTOR

Extract from a given long text input, eCommerce products and price budget.

### DISCLAIMER

This is not an "OpenAI wrapper", it use NLP(Natural Language Processing)
and tokens manipulations to 'understand the given input' then extract product
key name + budget.

Therefore, this is not optimized at all and was not tested on edge-cases.


### REQUIREMENTS

- python3 (>=3.10)
- [scapy](https://pypi.org/project/spacy)

### HOW TO INSTALL

```bash
pip install ector
```

### HOW TO USE

```bash
$ python
Python 3.12.9 (main, Feb  5 2025, 08:49:01) [GCC 9.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import json
>>> import asyncio
>>> from ector import extract
>>>
>>> text = "Hello, do you have some apple juice at 4 eur ? i only have 15 eur"
>>> print(json.dumps(asyncio.run(extract(text)), indent=2))
{
  "products": [
    {
      "product": "Apple juice",
      "price": 4.0,
      "currency": "eur"
    }
  ],
  "budget": {
    "price": 15.0,
    "currency": "eur"
  }
}
>>>
```

### AUTHOR

- Sanix-Darker

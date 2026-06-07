# Testing 02 — Test Matrix

Legend: **E** existing (must stay green), **N** new regression/unit test.

## Integration (`tests/test_extract.py`)
| # | Input | Expected | Type |
|---|-------|----------|------|
| E1 | "" | products=[], no budget | E |
| E2 | "I want to buy." | products=[] | E |
| E3 | "I'm looking for a new laptop." | [{product:"New laptop"}] | E |
| E4 | "I want a smartphone for 200 USD." | [{Smartphone,200,usd}], no budget | E |
| E5 | "My budget is 300 USD." | products=[], budget 300 usd | E |
| E6 | "I only have 150 eur." | products=[], budget 150 eur | E |
| E7 | "big TV. gaming console. budget 1200 USD." | 2 products, budget 1200 usd | E |
| E8 | "looking for a camera. my budget is 500 usd." | [Camera], budget 500 usd | E |
| E9 | "phone. budget is abc or 12x34" | [Phone], no budget | E |
| E10 | "laptop for 500 usd or 600 eur." | [{...,500,usd}], no budget | E |
| E11 | "phone for 250" | [{Phone,250}], no currency, no budget | E |

## New regression (post-fix)
| # | Input | Expected | Bug/Risk |
|---|-------|----------|----------|
| N1 | "I want a pound cake." | [{product:"Pound cake"}] | RISK-009 |
| N2 | "I want 2 phones." | [{product:"Phones", quantity:2}] no price | BUG-010 |
| N3 | "My budget is 300." | products=[], budget {price:300.0} (no currency) | BUG-008 |
| N4 | "je n'ai que 50 euros." (fr) | products=[], budget 50 eur | BUG-001 |
| N5 | "I will forget the milk." | 'forget' must NOT count as trigger 'get' | BUG-009 |
| N6 (fr) | "je veux un iPhone noir." | product contains "iPhone" (elision intact) | BUG-014 |

## Unit — money (`tests/test_money.py`)
| Input | parse_price → | Note |
|-------|---------------|------|
| "It's 25$" | (25.0, "usd") | symbol after |
| "$25" | (25.0, "usd") | symbol before |
| "25 eur" | (25.0, "eur") | code |
| "500 Rupees" | (500.0, "inr") | word |
| "300 yen" | (300.0, "jpy") | word→code |
| "no price" | (None, None) | none |
| "2 phones" (allow_bare=False) | (None, None) | quantity |
| is_currency_only("usd") | True | full match |
| is_currency_only("pound cake") | False | substring guard fix |

## Unit — triggers (`tests/test_triggers.py`)
| Text | contains_trigger | Note |
|------|------------------|------|
| "I need a phone" | True | 'need' |
| "I will forget it" | False | not 'get' in 'forget' |
| "that is awesome" | False | not 'some' in 'awesome' |
| "my budget is set" | False(as trigger) | not 'get' in 'budget' |

## Unit — dictionary validation (`tests/test_dictionary.py`)
- No entry contains a doubled token like "somesome" or "desje".
- All lists are unique after normalization.
- All lists are lowercase/stripped.

## Unit — text_utils (`tests/test_text_utils.py`)
- `normalize_text("j'ai un budget")` keeps the apostrophe.
- `normalize_text("9.99")` keeps the decimal.
- `clean_phrase("i need a big red apple", fillers)` → "Big red apple".
- `clean_phrase("the laptop", [])` → "Laptop".

## Component — models (`tests/test_models.py`)
- Calling `get_model` twice triggers `spacy.load` once (spy/patch).

## CLI (`tests/test_cli.py`)
- `main(["I want a laptop for 150 usd"])` prints JSON with a product.
- `--lang fr` path works.

## Coverage goal
Every BUG-xxx and RISK-xxx in the audit maps to at least one row above.

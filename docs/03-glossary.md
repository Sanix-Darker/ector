# 03 — Glossary

| Term | Meaning in ECTOR |
|------|------------------|
| **Trigger** | A word/phrase indicating a purchase intent (e.g. "looking for", "i need", "do you have"). Presence steers a sentence toward product extraction. |
| **Filler** | A leading phrase to strip from a product phrase (e.g. "i want a", "je voudrais un") so the result is the bare product name. |
| **Budget hint** | A phrase implying a spending ceiling (e.g. "i only have", "my budget is", "je n'ai que"). |
| **Product token** | A spaCy token (NOUN/PROPN) identified as the head of a product mention. |
| **Product phrase** | The product token plus its descriptive modifiers, e.g. "big red apple". |
| **MONEY entity** | A spaCy named entity labelled `MONEY`. |
| **Currency code** | Normalized lowercase code: `usd`, `eur`, `gbp`, `cad`, `aud`, `inr`, `jpy`, `chf`, `krw`, `sar`, `aed`. |
| **Span / Sent** | A spaCy `Span`; `doc.sents` yields sentence spans. |
| **dep_** | spaCy dependency relation label (e.g. `dobj`, `pobj`, `conj`). |
| **pos_** | spaCy coarse part-of-speech tag (e.g. `NOUN`, `PROPN`, `VERB`). |
| **lemma_** | The base form of a token (e.g. "buying" → "buy"). |
| **Heuristic** | A rule-of-thumb decision, not guaranteed correct, used here to classify sentences as product vs. budget. |

## spaCy dependency labels referenced in code

- `dobj` / `obj` — direct object of a verb.
- `pobj` — object of a preposition.
- `attr` — attribute/subject complement (with a copula like "be"/"être").
- `expl` — expletive ("there" / "il").
- `conj` / `cc` — conjuncts and coordinating conjunctions ("and", "et").
- `punct` — punctuation.

These labels differ between English and French models; the target design keeps
language-specific assumptions explicit rather than implicit.

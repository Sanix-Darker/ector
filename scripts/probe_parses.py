"""Probe spaCy parses for cases that drive products.py design."""
import spacy

nlp_en = spacy.load("en_core_web_sm")
nlp_fr = spacy.load("fr_core_news_sm")


def dump(nlp, text):
    print(f"\n=== {text!r} ===")
    doc = nlp(text)
    for tok in doc:
        print(
            f"  {tok.text:<14} pos={tok.pos_:<6} dep={tok.dep_:<10} "
            f"head={tok.head.text:<12} lemma={tok.lemma_}"
        )


for t in [
    "I want 2 phones.",
    "I want a phone for 250",
    "I'm looking for a new laptop.",
    "I want a pound cake.",
    "I want a smartphone for 200 USD.",
    "I'm looking for a big TV.",
    "I also need a gaming console.",
]:
    dump(nlp_en, t)

for t in [
    "je veux un iPhone noir.",
    "je veux un iPhone noire et aussi des Jordans.",
]:
    dump(nlp_fr, t)

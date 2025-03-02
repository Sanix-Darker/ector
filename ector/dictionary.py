import re

ENGLISH = "en"
FRENCH = "fr"

########################
# ENGLISH TRIGGERS
########################
REQUEST_TRIGGERS_EN = [
    # Existing ones
    "some",
    "looking for", "looking to buy", "looking to purchase",
    "searching for", "interested in", "do you have", "do you sell",
    "is there", "are there", "would like", "would love",
    "can you find", "could you find", "find me", "show me", "give me",
    "can you suggest", "could you suggest", "can you recommend", "could you recommend",
    "what is the price of", "how much is", "how much are", "how much for",
    "buy", "purchase", "need", "want", "require", "find", "get", "sell", "have",
    "suggest", "recommend", "show", "maybe", "maybe?",
    "wish to buy", "wish to order", "plan to purchase", "i'm in the market for",
    "hoping to buy", "consider buying", "in need of", "seeking", "eager to acquire",
    "where can i find", "intent to order", "looking up pricing", "checking cost",
    "thinking of buying", "shopping for", "add to cart", "add item", "add product",
    "available for sale", "do you stock", "do you carry", "order now", "place an order",
    "get a quote", "quote me", "requesting price", "requesting availability",
    "is it available", "could i buy", "could i order", "looking to place an order",
    "looking to add", "how do i buy", "need pricing", "need costs", "compare prices",
    "purchase option", "purchase options", "looking for deals", "special offer",
    "intent to purchase", "ready to buy", "ready to purchase",

    # More expansions (typical e-commerce requests):
    "please check stock", "please check availability", "can i buy", "am i able to purchase",
    "would it be possible to get", "where can i purchase", "how do i purchase",
    "is it listed for sale", "on sale", "discount available", "checking offers",
    "any promotions", "any discount", "would i be able to get",
    "where do i find the price", "where is the price",
    "any cheaper options", "any bigger options", "any smaller options",
    "any new arrivals", "any best sellers", "bestsellers", "most popular items",
    "featured products", "featured item", "flash sale", "holiday sale", "clearance sale"
]

########################
# ENGLISH FILLER PHRASES
########################
FILLER_PHRASES_EN = [
    "i want a", "i want an", "i want some",
    "i need a", "i need an", "i need some",
    "i would like a", "i would like an", "i would like some",
    "i'd like a", "i'd like an", "i'd like some",
    "i wanna get a", "i wanna get an", "i wanna get some",
    "i am hoping to buy a", "i am hoping to buy an", "i am hoping to buy some",
    "i plan to purchase a", "i plan to purchase an", "i plan to purchase some",
    "i think i need a", "i think i need an", "i think i need some",
    "i was considering getting a", "i was considering getting an", "i was considering getting some",
    "i wonder if i can buy a", "i wonder if i can buy an", "i wonder if i can buy some",
    "i might get a", "i might get an", "i might get some",
    "i am trying to find a", "i am trying to find an", "i am trying to find some",
    "i'm trying to find a", "i'm trying to find an", "i'm trying to find some",
    "i would really like a", "i would really like an", "i would really like some",
    "i'm very interested in a", "i'm very interested in an", "i'm very interested in some",
    "i'm thinking about buying a", "i'm thinking about buying an", "i'm thinking about buying some",
    "i'm in need of a", "i'm in need of an", "i'm in need of some",
    "i believe i need a", "i believe i need an", "i believe i need some",
    "i guess i should buy a", "i guess i should buy an", "i guess i should buy some",
    "i guess i should get a", "i guess i should get an", "i guess i should get some",
    "it might be good to buy a", "it might be good to buy an", "it might be good to buy some",
    "i figure i need a", "i figure i need an", "i figure i need some",
    "i figure i should buy a", "i figure i should buy an", "i figure i should buy some",
    "i might pick up a", "i might pick up an", "i might pick up some",
    "i am leaning towards buying a", "i am leaning towards buying an", "i am leaning towards buying some",
    "i am leaning towards getting a", "i am leaning towards getting an", "i am leaning towards getting some",
    "i expect to purchase a", "i expect to purchase an", "i expect to purchase some",
    "i expect to buy a", "i expect to buy an", "i expect to buy some",
    "i expect to get a", "i expect to get an", "i expect to get some",
    "i intend to purchase a", "i intend to purchase an", "i intend to purchase some",
    "i intend to buy a", "i intend to buy an", "i intend to buy some",
    "i mean to acquire a", "i mean to acquire an", "i mean to acquire some",
    "i aim to buy a", "i aim to buy an", "i aim to buy some",
    "i am aiming to buy a", "i am aiming to buy an", "i am aiming to buy some",
    "i'm aiming to get a", "i'm aiming to get an", "i'm aiming to get some",
    "i was hoping to get a", "i was hoping to get an", "i was hoping to get some",
    "maybe i should buy a", "maybe i should buy an", "maybe i should buy some",
    "perhaps i need a", "perhaps i need an", "perhaps i need some",
    "perhaps i should get a", "perhaps i should get an", "perhaps i should get some",
    "i could use a", "i could use an", "i could use some",
    "i could really use a", "i could really use an", "i could really use some",
    "it would be nice to buy a", "it would be nice to buy an", "it would be nice to buy some"

    "some",
    "i need", "i want", "i would like", "i'd like", "i wanna",
    "i am looking for", "i'm looking for", "i am interested in", "i'm interested in",
    "i am searching for", "i'm searching for", "we need", "we want",
    "we are looking for", "we are interested in", "please", "could you", "can you", "would you",
    "show me", "find me", "get me", "give me", "do you have", "do you sell", "is there", "are there",
    "what is the price of", "what are the prices of", "how much is", "how much are", "how much for",
    "suggest", "recommend", "can you find", "could you find", "could you suggest", "could you recommend",
    "i'm in the market for", "i'm in need of", "i hope to get", "i plan to buy", "i think i might buy",
    "i was considering", "i was wondering if", "i'm hoping you have", "just checking if",
    "could it be possible", "any chance you have", "any possibility of", "would it be possible to",
    "looking to possibly", "just inquiring about", "let me know if you have", "is it in stock",
    "are they in stock", "would like to see", "would like to check", "i was curious about",
    "hoping you could", "wonder if i could", "i might need", "potentially might want",
    "wondering if available", "do i have the option", "can i see if", "can i see any", "please let me know",
    "would love to see", "would love to check", "i am hoping for", "i am hoping to get",

    "can i buy", "can i purchase", "am i able to purchase", "check stock for me",
    "check availability for me", "i was just browsing", "can you confirm if there's any discount",
    "do you know if there's a discount", "i was seeing if there's any promotion",
    "just verifying if i can purchase", "could i place the order", "would it be possible to place the order",
    "do you handle returns", "is there a return policy",
    "do you accept coupons", "can i apply a coupon", "do we have a discount code"
]

REQUEST_TRIGGERS_EN = [t.lower() for t in REQUEST_TRIGGERS_EN]
FILLER_PHRASES_EN   = [f.lower() for f in FILLER_PHRASES_EN]

########################
# FRENCH TRIGGERS
########################
REQUEST_TRIGGERS_FR = [
    "je cherche", "je suis intéressé par", "j'aimerais acheter",
    "est-ce que vous avez", "est-ce que vous vendez", "est-ce qu'il y a",
    "est-ce qu'il existe", "pourrais-je trouver", "peux-tu trouver",
    "montre-moi", "donne-moi", "je voudrais", "j'aimerais avoir", "acheter",
    "besoin", "veux", "voudrais", "trouver", "obtenir", "vendre", "avoir",
    "suggérer", "recommander", "montrer", "peut-être", "peutetre", "peutetre?",
    "je souhaite acheter", "je veux commander", "je prévois d'acquérir",
    "je compte acheter", "je regarde pour", "je recherche", "intéressé à acquérir",
    "où puis-je trouver", "je souhaite passer commande", "je souhaite obtenir",
    "comparer les prix", "je veux un devis", "j'aimerais un devis", "je veux une estimation",
    "est-ce disponible", "est-ce que c'est disponible", "est-ce que vous stockez",
    "proposez-vous", "avez-vous en vente", "besoin de commander", "besoin d'acheter",
    "j'ai l'intention d'acheter", "j'envisage d'acheter", "envisage d'acquérir",
    "demander un prix", "demander un tarif", "quelle est la disponibilité",
    "possible d'acheter", "possible de commander", "je regarde pour acheter",
    "je compte passer commande", "je désire acheter", "je désire commander",
    "achetons", "commandons", "obtention possible", "je ferais l'achat de",
    "je ferais la commande de", "est-il possible de", "peut-on se procurer",
    "je me demande si vous avez", "y a-t-il en stock", "disponible à la vente",
    "intéressé par l'achat", "je songe à acheter", "je songe à commander",
    "je voudrais passer commande",

    "pouvez-vous me trouver", "pouvez-vous me montrer", "je cherche à acheter",
    "je veux acquérir", "où se trouve", "où trouver", "quel est le tarif",
    "comment acheter", "comment puis-je acheter", "existe-t-il", "est-ce vendable",
    "est-ce soldé", "est-ce en promotion", "proposez-vous des réductions",
    "y a-t-il une réduction", "y a-t-il une promotion", "je regarde les offres",
    "je regarde les promotions", "je regarde les soldes", "avez-vous un rabais",
    "comment passer la commande", "peut-on commander maintenant",
    "je voudrais commander maintenant", "je peux acheter maintenant",
    "j'aimerais passer la commande", "peut-on finaliser l'achat",
    "j'aimerais finaliser l'achat", "j'aimerais finaliser l'achat"
]

########################
# FRENCH FILLER PHRASES
########################
FILLER_PHRASES_FR = [
    # Existing ones
    "je veux un", "je veux une", "je veux des",
    "je voudrais un", "je voudrais une", "je voudrais des",
    "j'aimerais un", "j'aimerais une", "j'aimerais des",
    "j'ai besoin d'un", "j'ai besoin d'une", "j'ai besoin de",
    "je songe à acquérir un", "je songe à acquérir une", "je songe à acquérir des",
    "je souhaite me procurer un", "je souhaite me procurer une", "je souhaite me procurer des",
    "je désire me procurer un", "je désire me procurer une", "je désire me procurer des",
    "j'ai envie de trouver un", "j'ai envie de trouver une", "j'ai envie de trouver des",
    "j'ai envie d'acheter un", "j'ai envie d'acheter une", "j'ai envie d'acheter des",
    "je prévois d'obtenir un", "je prévois d'obtenir une", "je prévois d'obtenir des",
    "je pense acheter un", "je pense acheter une", "je pense acheter des",
    "je pense acquérir un", "je pense acquérir une", "je pense acquérir des",
    "je compte acheter un", "je compte acheter une", "je compte acheter des",
    "je compte acquérir un", "je compte acquérir une", "je compte acquérir des",
    "je suis sur le point d'acheter un", "je suis sur le point d'acheter une",
    "je suis sur le point d'acheter des",
    "j'envisage de commander un", "j'envisage de commander une", "j'envisage de commander des",
    "j'aimerais commander un", "j'aimerais commander une", "j'aimerais commander des",
    "je voudrais passer une commande pour un", "je voudrais passer une commande pour une",
    "je voudrais passer une commande pour des",
    "je cherche à commander un", "je cherche à commander une", "je cherche à commander des",
    "je me demande si je peux acheter un", "je me demande si je peux acheter une",
    "je me demande si je peux acheter des",
    "je veux vraiment un", "je veux vraiment une", "je veux vraiment des",
    "je voudrais vraiment un", "je voudrais vraiment une", "je voudrais vraiment des",
    "j'aimerais vraiment un", "j'aimerais vraiment une", "j'aimerais vraiment des",
    "j'ai vraiment besoin d'un", "j'ai vraiment besoin d'une", "j'ai vraiment besoin de",
    "j'ai réellement besoin d'acheter un", "j'ai réellement besoin d'acheter une",
    "j'ai réellement besoin d'acheter des",
    "il me faut absolument un", "il me faut absolument une", "il me faut absolument des",
    "il me faudrait un", "il me faudrait une", "il me faudrait des",
    "je désire fortement un", "je désire fortement une", "je désire fortement des",
    "je projette d'acheter un", "je projette d'acheter une", "je projette d'acheter des",
    "je projette d'acquérir un", "je projette d'acquérir une", "je projette d'acquérir des",
    "j'ai l'intention précise d'acheter un", "j'ai l'intention précise d'acheter une",
    "j'ai l'intention précise d'acheter des",
    "je me dis que je devrais acheter un", "je me dis que je devrais acheter une",
    "je me dis que je devrais acheter des",
    "je réfléchis à acheter un", "je réfléchis à acheter une", "je réfléchis à acheter des",
    "je crois que je vais prendre un", "je crois que je vais prendre une",
    "je crois que je vais prendre des",
    "j'envisage sérieusement d'acheter un", "j'envisage sérieusement d'acheter une",
    "j'envisage sérieusement d'acheter des",
    "j'aurais besoin d'un", "j'aurais besoin d'une", "j'aurais besoin de",
    "je tenterais bien d'acheter un", "je tenterais bien d'acheter une",
    "je tenterais bien d'acheter des",
    "je me décide pour un", "je me décide pour une", "je me décide pour des",
    "j'ai la volonté d'acheter un", "j'ai la volonté d'acheter une",
    "j'ai la volonté d'acheter des"

    "je cherche", "je suis intéressé par", "j'aimerais acheter", "je veux",
    "je voudrais", "j'aimerais", "est-ce que vous avez", "est-ce que vous vendez",
    "est-ce qu'il y a", "est-ce qu'il existe", "peux-tu", "pourrais-tu", "pourriez-vous",
    "montre-moi", "donne-moi", "fais-moi", "combien coûte", "quel est le prix",
    "quel est son prix", "je regarde pour", "intéressé à acquérir", "où puis-je trouver",
    "je souhaite passer commande", "comparer les prix", "je veux un devis", "j'aimerais un devis",
    "je veux une estimation", "est-ce disponible", "est-ce que c'est disponible",
    "est-ce que vous stockez", "proposez-vous", "avez-vous en vente", "j'ai l'intention d'acheter",
    "j'envisage d'acheter", "demander un prix", "demander un tarif", "quelle est la disponibilité",
    "possible d'acheter", "possible de commander", "je regarde pour acheter",
    "je compte passer commande", "je désire acheter", "je désire commander",
    "achetons", "commandons", "obtention possible", "je ferais l'achat de",
    "je ferais la commande de", "peut-on se procurer", "je me demande si vous avez",
    "y a-t-il en stock", "disponible à la vente", "intéressé par l'achat",
    "je songe à acheter", "je songe à commander", "pourrais-je trouver",
    "peux-tu trouver", "peut-être", "peutetre", "peutetre?", "suggérer",
    "recommander", "montrer",

    "pouvez-vous me trouver", "pouvez-vous me montrer", "je cherche à acheter",
    "je veux acquérir", "où se trouve", "où trouver", "quel est le tarif", "comment acheter",
    "comment puis-je acheter", "existe-t-il", "est-ce vendable", "est-ce soldé", "est-ce en promotion",
    "proposez-vous des réductions", "y a-t-il une réduction", "y a-t-il une promotion",
    "je regarde les offres", "je regarde les promotions", "je regarde les soldes",
    "avez-vous un rabais", "comment passer la commande", "peut-on commander maintenant",
    "je voudrais commander maintenant", "je peux acheter maintenant",
    "j'aimerais passer la commande", "peut-on finaliser l'achat", "j'aimerais finaliser l'achat"
]

REQUEST_TRIGGERS_FR = [t.lower() for t in REQUEST_TRIGGERS_FR]
FILLER_PHRASES_FR   = [f.lower() for f in FILLER_PHRASES_FR]

########################
# BUDGET HINTS (ENGLISH)
########################
EN_BUDGET_HINTS = [
    "only have", "can only spend", "limit is", "my limit is", "maximum is", "max is",
    "i can't spend more than", "i cannot spend more than", "only got", "i only got",
    "i just have", "i've just got", "my budget is", "my total is", "spending cap is",
    "i can only afford", "my spending limit", "my max budget", "i do not want to exceed",
    "the highest i can pay", "the highest i can go", "the maximum i can go", "i can't exceed",
    "can't exceed", "can't go beyond", "won't go over", "budget limit", "imposed limit of",
    "i have to keep it under", "i must keep it under", "my budget does not exceed",
    "i plan to spend no more than", "i don't plan to spend more than", "i am restricted to",
    "i am constrained to", "i can't surpass",

    # More expansions
    "i have a budget of", "my budget cap is", "i won't go over", "i must not exceed",
    "i won't spend more than", "the maximum i want to spend", "the limit of my spending",
    "i do not intend to exceed", "the top of my budget", "my top budget",
    "the largest amount i can pay", "the biggest amount i can pay",
    "the largest sum i can go for", "the absolute limit of my spending",
    "my final limit is", "my end limit is",

    "i cannot allow myself to spend more than",
    "i can't stretch beyond",
    "it's out of my budget if it goes beyond",
    "i will not pay over",
    "my spending cannot exceed",
    "my spending won't exceed",
    "i cannot push my budget past",
    "the most i can allocate",
    "the highest amount i can allocate",
    "the biggest i can allocate",
    "the biggest i can manage to pay",
    "i will not manage more than",
    "i am unable to go beyond",
    "i have no possibility to exceed",
    "my finances won't allow more than",
    "the utmost i can pay",
    "the utmost i can stretch",
    "the maximum i am willing to put forth",
    "i will not invest more than",
    "i do not plan on going above",
    "cannot pass my ceiling of",
    "cannot pass my cap of",
    "i must cap my spending at",
    "my credit can't exceed",
    "i can only budget up to",
    "the upper bound of my spending is",
    "the upper limit of my spending is",
    "my final upper limit is",
    "my entire limit is",
    "i can't possibly go above",
    "the final boundary of my funds is",
    "my resources won't cover beyond",
    "the largest total i can commit is",
    "the largest financial outlay i can make is",
    "my final threshold is",
    "my threshold is",
    "the maximum i plan to outlay",
    "i can't push the envelope past",
    "i can't justify spending more than",
    "i can't justify going beyond",
    "my total spending won't exceed",
    "my final spending won't exceed",
    "my upper threshold is",
    "i must remain under",
    "cannot cross the limit of",
    "cannot cross my cap of",
    "i won't cross beyond",
    "the top expense i can handle is",
    "the peak i can afford is",
    "the peak of my budget is",
    "the absolute peak i can afford is",
    "i do not see myself spending above",
    "the biggest financial stretch i can do is",
    "my resources are limited to",
    "i must keep my purchase under",
    "my overall budget maximum",
    "my overall budget ceiling",
    "i am not willing to exceed",
    "i don't want to push it beyond",
    "i won't push it beyond",
    "i have absolutely no means to surpass",
    "cannot surpass the boundary of",
    "my credit line won't allow more than",
    "my card won't allow beyond",
    "my final spending maximum is",
    "my last possible limit is",
    "the final sum i can pay is",
    "the final sum i can offer is",
    "the final sum i can manage is",
    "the total sum i can manage won't go beyond",
    "the boundary of my payment is",
    "the ceiling of my budget is",
    "the apex of what i can spend is",
    "the apex of my financial limit is",
    "the pinnacle of my spending is",
    "the maximum i can handle",
    "the maximum i can muster",
    "the largest i can muster financially",
    "the budget line i can't cross",
    "my biggest budget line is",
    "this is as high as i can go",
    "this is as far as i can go financially",
    "there is no going beyond this point for me",
    "i must not go above",
    "the cost cannot go above my set limit of",
    "i have fixed my cap at",
    "my absolute spending boundary is",
    "my absolute budget restriction is",
    "my absolute budget boundary is",
    "the absolute highest i can pay is",
    "the absolute highest i can stretch is",
    "the absolute highest i can manage is",
    "cannot pay more than",
    "impossible for me to pay more than",
    "i have zero capability to go above",
    "i have zero flexibility past",
    "the cost barrier for me is",
    "my final spending frontier is",
    "my locked spending limit is",
    "i won't allow myself to go over",
    "my personal spending max is",
    "my personal spending boundary is",
    "my personal financial limit is",
]

########################
# BUDGET HINTS (FRENCH)
########################
FR_BUDGET_HINTS = [
    "je n'ai que", "ma limite", "mon budget", "je ne peux dépenser",
    "je ne peux que dépenser", "limite de", "limite est", "ma limite est",
    "maximum est", "je ne peux pas dépasser", "je n'ai pas plus de", "je n'ai pas au-delà de",
    "je ne vais pas dépasser", "je ne veux pas dépasser", "je ne peux pas aller au-delà de",
    "je ne peux plus", "je ne vais pas aller au-dessus de", "je ne vais pas aller plus loin que",
    "mon plafond de dépense", "mon plafond est", "je ne veux pas aller plus haut que",
    "je suis limité à", "je suis contraint à", "ma contrainte est de", "je ne dois pas dépasser",
    "je ne passerai pas au-dessus de", "je dois rester sous", "je compte rester sous",
    "je ne souhaite pas dépenser plus de", "je n'ai pas le budget pour dépasser",
    "je suis obligé de rester sous", "limite de mon budget", "je ne dispose que de",
    "je ne peux aller au-delà",

    # More expansions
    "je dispose d'un budget de", "mon budget maximum est", "mon budget max est", "je ne dépenserai pas plus de",
    "je ne compte pas dépasser", "le maximum que je puisse dépenser", "mon plus haut budget",
    "la plus grande somme que je peux payer", "ma limite finale est", "mon budget final est",
    "je ne compte pas aller plus loin", "je ne désire pas dépasser",
    "mon budget ne doit pas être dépassé", "mon plafond ne doit pas être franchi",
    "je ne dépasserai jamais",
    "je ne souhaite pas aller au-delà de",
    "je ne peux pas envisager plus de",
    "mon seuil de dépense est",
    "mon seuil maximal est",
    "ma limite maximale",
    "je ne pourrais pas mettre plus de",
    "je ne compte vraiment pas dépasser",
    "la plus grande somme que je peux investir est",
    "la plus haute somme que je peux investir est",
    "le plus gros montant que je puisse payer est",
    "je ne paierai pas au-dessus de",
    "je ne paierai jamais plus de",
    "mon budget ne me permet pas d'aller plus loin que",
    "mon budget ne me permet pas de dépasser",
    "ma capacité financière s'arrête à",
    "ma limite absolue est",
    "le maximum que je suis prêt à dépenser est",
    "le maximum que je suis en mesure de dépenser est",
    "le plafond financier que je ne dépasserai pas",
    "je dois absolument rester sous la barre de",
    "je ne pourrai pas franchir la barre de",
    "c'est au-dessus de ce que je peux me permettre",
    "je suis incapable de dépenser plus de",
    "je refuse de mettre plus que",
    "je ne mettrai jamais davantage que",
    "je n'ai pas les moyens d'aller au-delà de",
    "mon budget ne couvre pas plus que",
    "je suis restreint à",
    "je suis limité financièrement à",
    "je n'ai pas la marge pour aller plus loin que",
    "je ne dépasserai pas ma limite financière de",
    "mon enveloppe budgétaire s'arrête à",
    "c'est hors de mon budget si je dépasse",
    "je ne franchirai pas la limite de",
    "la limite budgétaire que je me suis fixée est",
    "je ne vais pas franchir la limite de",
    "je ne tolèrerai pas de dépenser au-delà de",
    "il m'est impossible de verser plus de",
    "je ne souhaite pas faire un effort au-dessus de",
    "ma limite ne me laisse pas dépasser",
    "ma contrainte budgétaire est strictement",
    "je dois maintenir mes dépenses sous",
    "je ne passerai pas au-dessus de ce seuil",
    "ma marge de dépense maximale est",
    "la somme maximale que je peux aligner est",
    "mon seuil financier maximal est",
    "je ne pourrai pas assumer un montant supérieur à",
    "c'est hors de portée si ça dépasse",
    "je dois me cantonner à",
    "je dois me limiter strictement à",
    "je ne peux pas monter au-delà de",
    "mon plafond budgétaire total est",
    "je n'ai pas la possibilité de payer plus de",
    "je ne paierai pas plus qu'un total de",
    "mon total à ne pas dépasser est",
    "ma limite stricte est",
    "je ne ferai pas un achat plus élevé que",
    "mon budget prévu est de maximum",
    "le total que je peux engager ne doit pas dépasser",
    "je ne pourrais pas couvrir une somme au-delà de",
    "je serais en difficulté si je dépasse",
    "j'ai un cap financier fixé à",
    "c'est ma limite budgétaire absolue",
    "je ne ferai pas de dépassement au-delà de",
    "je ne dois en aucun cas aller plus haut que",
    "il m'est impensable de dépenser plus que",
    "je me suis imposé un plafond de",
    "je dois impérativement rester sous",
    "je ne prévois aucun dépassement de",
    "je ne veux pas allonger davantage que",
    "je reste borné à",
    "je reste contraint à",
    "je reste enfermé dans une limite de",
    "je reste fermement décidé à ne pas dépasser",
    "je ne ferai aucun excès au-delà de",
    "je ne franchirai pas ce seuil budgétaire",
    "mon budget global ne dépassera pas",
    "mon total ne surpassera pas",
    "je n'envisage pas d'aller plus loin que",
    "je me fixe un maximum de",
    "je bloque mes dépenses à",
    "je verrouille mes dépenses à",
    "j'ai établi un seuil de",
    "ma ligne budgétaire maximale se situe à",
    "la somme la plus haute que je paierai est",
    "je n'ai pas d'élasticité financière pour aller au-delà de",
    "mon effort financier maximum est",
    "je ne fournirai pas plus que",
    "je ne veux pas mettre davantage que",
    "c'est hors de mes moyens de dépasser",
    "j'ai décrété que je resterai en dessous de",
    "je refuse catégoriquement de dépasser",
    "je mets un stop à mes dépenses au-delà de",
    "il n'est pas question de surmonter",
    "je m'arrête à",
    "j'ai imposé un garde-fou à",
    "je ne saurais me permettre plus que",
    "je ne prévois pas de débourser plus de",
    "je stopperai mes achats si ça dépasse",
    "c'est un frein si on dépasse",
    "ma limite budgétaire se situe à"
]

########################
# CURRENCY PATTERNS
########################
CURRENCY_ONLY_PATTERN = re.compile(
    r"(usd|eur|gbp|cad|aud|inr|jpy|chf|krw|sar|dirham|dhs|"
    r"dollars?|euros?|pounds?|yen|rupees?|\$|€|£)",
    re.IGNORECASE,
)

MONEY_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)(?:\s*(usd|eur|gbp|cad|aud|inr|jpy|chf|krw|sar|dirham|dhs|"
    r"dollars?|euros?|pounds?|yen|rupees?|\$|€|£))?",
    re.IGNORECASE,
)

CURRENCY_MAP = {
    "$": "usd",
    "dollar": "usd",
    "dollars": "usd",
    "usd": "usd",
    "€": "eur",
    "eur": "eur",
    "euro": "eur",
    "euros": "eur",
    "£": "gbp",
    "pound": "gbp",
    "pounds": "gbp",
    "gbp": "gbp",
    "cad": "cad",
    "aud": "aud",
    "inr": "inr",
    "jpy": "jpy",
    "yen": "jpy",
    "chf": "chf",
    "krw": "krw",
    "sar": "sar",
    "dirham": "aed",
    "dhs": "aed",
    "rupee": "inr",
    "rupees": "inr",
}

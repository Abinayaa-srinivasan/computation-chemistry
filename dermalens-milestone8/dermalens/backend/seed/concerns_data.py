"""Skin-concern guidance for DermaLens.

General, widely taught skincare guidance written for learning. It is NOT personal medical advice and
it is not a clinical guideline; verify with a dermatologist before relying on it (the app says so).

Each ingredient entry: (INCI name in the ingredient table, priority 1-3, why it helps,
how to use it, caution or "").  Priority 3 = first-line, 2 = good option, 1 = supporting.
"""

CONCERNS = {
    "pigmentation": {
        "label": "Pigmentation and dark spots",
        "description": "Uneven tone, sun spots, post-acne marks and melasma-type patches.",
        "ingredients": [
            ("Glycolic Acid", 3, "An AHA that sheds pigmented surface cells and brightens.", "Start 2 nights a week in the evening, then build up if skin stays comfortable.", "Raises sun sensitivity; skip on irritated skin."),
            ("Ascorbic Acid", 3, "Vitamin C blocks pigment production and protects against sun damage.", "Use in the morning on clean skin, before sunscreen.", "Can sting; start with a lower strength."),
            ("Niacinamide", 3, "Slows pigment transfer to skin cells and strengthens the barrier.", "Once or twice daily; pairs well with most ingredients.", ""),
            ("Azelaic Acid", 3, "Reduces pigment and calms redness; good for post-acne marks.", "Once or twice daily after cleansing.", "Mild tingling is common at first."),
            ("Tranexamic Acid", 2, "Helps fade stubborn patches such as melasma-type pigment.", "Daily, morning or evening, under moisturiser or sunscreen.", ""),
            ("Arbutin", 2, "Gently slows pigment production.", "Once or twice daily.", ""),
            ("Kojic Acid", 1, "Brightens dark spots.", "Evenings, a few times a week.", "Can sensitise some skin."),
            ("Zinc Oxide", 1, "Mineral sun filter; sunscreen is essential because sun makes pigment worse.", "Apply as the last morning step every day and reapply outdoors.", ""),
        ],
        "avoid": [
            ("Skipping sunscreen", "UV light darkens existing spots and undoes progress."),
            ("Fragrance and essential oils", "Irritation can trigger more dark marks, especially in deeper skin tones."),
            ("Harsh scrubs", "Inflammation from rubbing can cause new pigment."),
        ],
        "tips": ["Fading usually takes 8 to 12 weeks, so give a routine time before switching.", "Wear a broad-spectrum SPF 30+ sunscreen every day."],
    },
    "acne": {
        "label": "Acne and breakouts",
        "description": "Pimples, blackheads and whiteheads.",
        "ingredients": [
            ("Salicylic Acid", 3, "A BHA that dissolves oil inside pores and clears blackheads.", "Once daily to start, as a cleanser, toner or leave-on treatment.", "Can dry skin; check with a doctor if pregnant."),
            ("Benzoyl Peroxide", 3, "Kills acne bacteria and reduces inflamed pimples.", "Use a low strength on spots or the whole area once daily.", "Dries and irritates; bleaches fabric."),
            ("Niacinamide", 3, "Calms inflammation and helps control oil.", "Once or twice daily.", ""),
            ("Azelaic Acid", 2, "Reduces bacteria, clogged pores and the marks pimples leave behind.", "Once or twice daily.", ""),
            ("Zinc PCA", 2, "Helps balance oil and has a mild antibacterial effect.", "Daily in a serum or gel.", ""),
            ("Retinol", 2, "Keeps pores from clogging and speeds renewal.", "Start twice a week in the evening.", "Not for use in pregnancy; can irritate."),
            ("Melaleuca Alternifolia Leaf Oil", 1, "Tea tree oil has some antibacterial action on spots.", "Only in a properly diluted product, on spots.", "Essential oil that can irritate or cause allergy."),
        ],
        "avoid": [
            ("Coconut oil and isopropyl myristate", "Rated high for blocking pores in many people."),
            ("Heavy occlusive creams on the face", "Thick formulas can trap oil in acne-prone skin."),
            ("Over-washing and harsh scrubs", "Stripping skin makes it produce more oil and irritates active acne."),
        ],
        "tips": ["Use one new active at a time and wait 2 to 4 weeks before judging it.", "See a dermatologist for painful, cystic or scarring acne."],
    },
    "dryness": {
        "label": "Dryness and tightness",
        "description": "Flaky, rough or tight skin that lacks water or oil.",
        "ingredients": [
            ("Glycerin", 3, "A humectant that draws water into the skin.", "Apply to damp skin and seal with moisturiser.", ""),
            ("Sodium Hyaluronate", 3, "Holds water on the skin surface for plumper, softer skin.", "Apply on damp skin, then a moisturiser on top.", ""),
            ("Ceramide NP", 3, "A skin-identical lipid that rebuilds the moisture barrier.", "Use in a daily moisturiser, morning and night.", ""),
            ("Squalane", 2, "A light oil that softens without a heavy feel.", "A few drops or in a cream, once or twice daily.", ""),
            ("Urea", 2, "Hydrates and gently softens rough patches.", "Daily in a cream, especially on dry areas.", "Can sting on cracked skin."),
            ("Panthenol", 2, "Hydrates and helps the barrier heal.", "Daily in serums or creams.", ""),
            ("Petrolatum", 1, "Seals in moisture very effectively.", "A thin layer as the last evening step.", "Can feel heavy."),
            ("Butyrospermum Parkii Butter", 1, "Rich plant butter that softens very dry skin.", "Night creams and balms.", ""),
        ],
        "avoid": [
            ("Alcohol Denat. and strong sulfate cleansers", "They strip oils and worsen tightness."),
            ("Very hot showers", "Hot water removes natural oils."),
        ],
        "tips": ["Moisturise within 3 minutes of washing while skin is still damp."],
    },
    "ageing": {
        "label": "Fine lines and ageing",
        "description": "Fine lines, loss of firmness and rough texture.",
        "ingredients": [
            ("Retinol", 3, "The best-studied ingredient for smoothing lines and boosting renewal.", "Start twice a week in the evening, add nights slowly.", "Not for use in pregnancy; can irritate."),
            ("Bakuchiol", 2, "A gentler plant alternative that gives some retinol-like benefits.", "Daily, morning or evening.", ""),
            ("Ascorbic Acid", 3, "Vitamin C protects against free-radical damage and supports firmness.", "Use in the morning before sunscreen.", "Can sting."),
            ("Niacinamide", 2, "Improves barrier strength and the look of texture.", "Once or twice daily.", ""),
            ("Palmitoyl Tripeptide-1", 2, "A signalling peptide used for firmer-looking skin.", "Daily in a serum or cream.", ""),
            ("Copper Tripeptide-1", 1, "A copper peptide used for firmness and repair.", "Daily in a serum.", "Keep apart from strong acids and vitamin C."),
            ("Sodium Hyaluronate", 2, "Plumps the look of fine lines by hydrating.", "On damp skin, then moisturiser.", ""),
            ("Ferulic Acid", 1, "An antioxidant that boosts the effect of vitamins C and E.", "In a morning antioxidant serum.", ""),
            ("Zinc Oxide", 2, "Mineral sun filter; sun damage is the biggest cause of visible ageing.", "Every morning as the last step.", ""),
        ],
        "avoid": [
            ("Skipping sunscreen", "UV light is the main driver of wrinkles and spots."),
            ("Using many strong actives at once", "Too much exfoliation damages the barrier and ages skin faster."),
        ],
        "tips": ["Sunscreen every day matters more than any anti-ageing serum.", "Results from retinoids take about 12 weeks."],
    },
    "dark circles": {
        "label": "Dark circles",
        "description": "Shadowy or bluish-brown skin under the eyes.",
        "ingredients": [
            ("Caffeine", 3, "Constricts small blood vessels and reduces puffiness.", "Use an eye product morning and night, patting gently.", ""),
            ("Ascorbic Acid", 2, "Brightens pigment-type dark circles.", "Morning, in an eye-safe product.", "The eye area is thin and can sting."),
            ("Niacinamide", 2, "Helps even tone and strengthens thin skin.", "Daily.", ""),
            ("Tranexamic Acid", 2, "May help pigment-type dark circles.", "Daily in an eye-safe formula.", ""),
            ("Sodium Hyaluronate", 1, "Hydrates thin skin, making hollows less noticeable.", "Daily on damp skin.", ""),
        ],
        "avoid": [
            ("Rubbing the eye area", "Friction darkens and thins the skin."),
            ("Fragrance and essential oils near the eyes", "The skin there is thin and reacts easily."),
        ],
        "tips": ["Sleep, genetics and shadowing from hollows also cause dark circles, and no product fixes those.", "Wear sunscreen and sunglasses."],
    },
    "redness": {
        "label": "Redness and irritation",
        "description": "Flushed, blotchy or easily reddened skin.",
        "ingredients": [
            ("Azelaic Acid", 3, "Calms redness, including rosacea-type redness.", "Once or twice daily.", "Mild tingling is common at first."),
            ("Centella Asiatica Extract", 3, "Soothes and supports healing.", "Daily in a serum or cream.", ""),
            ("Madecassoside", 2, "An active from centella that calms irritated skin.", "Daily.", ""),
            ("Niacinamide", 2, "Strengthens the barrier and reduces blotchiness.", "Once daily at a low strength to start.", ""),
            ("Allantoin", 2, "Soothes and softens.", "Daily.", ""),
            ("Bisabolol", 1, "Chamomile-derived calming ingredient.", "Daily.", ""),
            ("Panthenol", 2, "Calms and hydrates.", "Daily.", ""),
            ("Zinc Oxide", 1, "A mineral sunscreen filter that is gentle on reactive skin.", "Every morning.", ""),
        ],
        "avoid": [
            ("Alcohol Denat.", "Drying and can trigger flushing."),
            ("Fragrance and essential oils", "Frequent irritants for reactive skin."),
            ("Strong acids and scrubs", "Make redness worse."),
        ],
        "tips": ["See a doctor if redness comes with burning, bumps or flares, as it may be rosacea."],
    },
    "oiliness": {
        "label": "Oily skin and shine",
        "description": "Excess shine and a greasy feel.",
        "ingredients": [
            ("Niacinamide", 3, "Helps regulate oil and reduces the look of pores.", "Once or twice daily.", ""),
            ("Salicylic Acid", 3, "Cleans out oil in pores.", "Once daily to start.", "Can dry skin."),
            ("Zinc PCA", 2, "Helps balance oil production.", "Daily in a light serum.", ""),
            ("Silica", 1, "A powder that absorbs oil and mattifies.", "In mattifying moisturisers and primers.", ""),
            ("Kaolin", 1, "Clay that absorbs oil.", "In a mask once or twice a week.", "Can dry skin if overused."),
            ("Camellia Sinensis Leaf Extract", 1, "Green tea extract with mild oil-balancing and calming effects.", "Daily.", ""),
        ],
        "avoid": [
            ("Skipping moisturiser", "Dehydrated skin often makes even more oil."),
            ("Heavy oils and butters", "Can add to the greasy feel."),
            ("Over-cleansing", "Stripping skin triggers rebound oil."),
        ],
        "tips": ["Choose a light, oil-free gel moisturiser; oily skin still needs hydration."],
    },
    "dullness": {
        "label": "Dullness and uneven texture",
        "description": "Tired-looking skin that lacks glow.",
        "ingredients": [
            ("Glycolic Acid", 3, "Sheds dull surface cells so skin reflects more light.", "Start 1 to 2 nights a week.", "Raises sun sensitivity."),
            ("Lactic Acid", 3, "A gentler AHA that exfoliates and hydrates.", "Start 1 to 2 nights a week.", "Raises sun sensitivity."),
            ("Gluconolactone", 2, "A very gentle PHA exfoliant.", "A few times a week or daily if tolerated.", ""),
            ("Ascorbic Acid", 3, "Brightens and protects against pollution and UV damage.", "Mornings, before sunscreen.", "Can sting."),
            ("Niacinamide", 2, "Evens tone and improves the look of texture.", "Once or twice daily.", ""),
            ("Sodium Ascorbyl Phosphate", 1, "A gentler, stable vitamin C.", "Mornings.", ""),
            ("Mandelic Acid", 1, "A mild AHA that suits sensitive skin better.", "A few times a week.", ""),
        ],
        "avoid": [
            ("Over-exfoliating", "Too many acids and scrubs damage the barrier and make skin duller."),
        ],
        "tips": ["Exfoliate 1 to 3 times a week at most, and use sunscreen daily."],
    },
    "large pores": {
        "label": "Large-looking pores",
        "description": "Visible pores, often on the nose and cheeks.",
        "ingredients": [
            ("Salicylic Acid", 3, "Clears oil and debris that make pores look bigger.", "Once daily to start.", "Can dry skin; check with a doctor if pregnant."),
            ("Niacinamide", 3, "Improves the look of pore size over weeks.", "Once or twice daily.", ""),
            ("Retinol", 2, "Boosts renewal and can tighten the look of pores.", "Twice a week in the evening to start.", "Not for use in pregnancy; can irritate."),
            ("Glycolic Acid", 2, "Smooths surface texture.", "1 to 2 nights a week.", "Raises sun sensitivity."),
            ("Kaolin", 1, "Absorbs oil that exaggerates pores.", "Weekly mask.", ""),
        ],
        "avoid": [
            ("Pore strips and squeezing", "They can stretch pores and cause scarring."),
        ],
        "tips": ["Pore size is mostly genetic, so products only change how visible pores look."],
    },
    "sensitivity": {
        "label": "Sensitive skin",
        "description": "Skin that stings, burns or reacts to many products.",
        "ingredients": [
            ("Centella Asiatica Extract", 3, "Calms and supports skin repair.", "Daily.", ""),
            ("Panthenol", 3, "Soothes and strengthens the barrier.", "Daily.", ""),
            ("Ceramide NP", 3, "Rebuilds a weak barrier.", "Daily moisturiser.", ""),
            ("Allantoin", 2, "Soothes and softens.", "Daily.", ""),
            ("Glycerin", 2, "Gentle hydration.", "Daily.", ""),
            ("Gluconolactone", 2, "A very gentle exfoliant for sensitive skin.", "Once or twice a week.", ""),
            ("Bisabolol", 1, "Calming ingredient.", "Daily.", ""),
            ("Avena Sativa Kernel Extract", 2, "Oat extract that eases itch and dryness.", "Daily.", ""),
            ("Zinc Oxide", 2, "A mineral sunscreen filter that is gentle on sensitive skin.", "Every morning.", ""),
        ],
        "avoid": [
            ("Fragrance and essential oils", "Common triggers of reactions."),
            ("Alcohol Denat.", "Drying and irritating."),
            ("Strong acids and retinol", "Often too harsh until the barrier is healthy."),
        ],
        "tips": ["Patch-test every new product behind the ear for 2 to 3 days.", "Introduce one product at a time."],
    },
}

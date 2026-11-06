"""Seed ingredient data for DermaLens.

Format (one ingredient per line, fields separated by "|"):
INCI name | aliases (;) | categories (;) | description | irritancy 0-5 | comedogenic 0-5 |
flags (;) | suited skin types (;) | incompatible with (;) | typical min % | typical max %

IMPORTANT (honesty rule): min/max are APPROXIMATE typical usage ranges from general
cosmetic-formulation knowledge. They are NOT the exact amount in any specific product.
Replace with verified data (e.g. EU CosIng, supplier datasheets, SCCS opinions) for production.
Flags: allergen, fragrance, drying_alcohol, paraben, sulfate, essential_oil, silicone,
pregnancy_caution, sensitive_caution.
Irritancy / comedogenic ratings are rough educational estimates, 0 = none.
"""

RANGE_SOURCE = (
    "Approximate typical usage range from general cosmetic-formulation knowledge; "
    "sample data, verify before relying on it."
)

RAW = """
Water|Aqua;Eau|Solvent|The base of most products; dissolves other ingredients.|0|0||all||40|90
Glycerin|Glycerol;Glycerine|Humectant|Draws water into the skin's top layer to keep it hydrated.|0|0||all||2|10
Butylene Glycol|1,3-Butanediol|Humectant;Solvent|Light humectant and solvent that helps other ingredients absorb.|1|1||all||1|10
Propylene Glycol||Humectant;Solvent|Humectant and solvent; can irritate some sensitive skin.|1|0|sensitive_caution|all||1|10
Propanediol|1,3-Propanediol|Humectant;Solvent|Plant-derived solvent and humectant, gentle for most skin.|0|0||all||1|10
Pentylene Glycol|1,2-Pentanediol|Humectant;Preservative|Humectant that also boosts preservative systems.|0|0||all||1|5
Sodium Hyaluronate|Hyaluronic Acid;Sodium Hyaluronate Crosspolymer|Humectant|Holds large amounts of water on the skin surface.|0|0||all||0.01|2
Panthenol|Provitamin B5;Dexpanthenol|Humectant;Soothing agent|Hydrates and calms; helps the skin barrier.|0|0||all;dry;sensitive||0.5|5
Urea|Carbamide|Humectant;Exfoliant|Hydrates at low levels and gently softens rough skin at higher levels.|1|0|sensitive_caution|dry||2|10
Sodium PCA||Humectant|Natural moisturising factor that binds water.|0|0||all||0.5|5
Sorbitol||Humectant|Sugar alcohol that attracts moisture.|0|0||all||1|10
Betaine|Trimethylglycine|Humectant;Soothing agent|Hydrating, helps reduce irritation from other ingredients.|0|0||all||1|5
Allantoin||Soothing agent|Calms and softens skin.|0|0||all;sensitive||0.1|0.5
Squalane||Emollient|Light, skin-like oil that softens without feeling heavy.|0|1||all||1|10
Caprylic/Capric Triglyceride|Coconut-derived triglyceride|Emollient|Light, silky emollient.|0|1||all||2|15
Cetearyl Alcohol||Emollient;Thickener;Emulsifier|Fatty alcohol (not drying) that thickens creams and softens skin.|0|2||all||1|8
Cetyl Alcohol||Emollient;Thickener|Fatty alcohol that adds richness and body.|0|2||all||0.5|5
Stearyl Alcohol||Emollient;Thickener|Fatty alcohol that thickens and softens.|0|2||all||0.5|5
Stearic Acid||Emollient;Emulsifier;Thickener|Fatty acid that helps form creamy textures.|0|2||all||1|5
Dimethicone||Occlusive;Emollient|Silicone that smooths skin and forms a light protective film.|0|1|silicone|all||0.5|20
Cyclopentasiloxane||Emollient;Solvent|Volatile silicone that spreads easily then evaporates.|0|1|silicone|all||1|30
Phenyl Trimethicone||Emollient|Silicone that adds slip and shine.|0|1|silicone|all||1|10
Amodimethicone||Emollient;Film-former|Conditioning silicone used mostly in hair care.|0|1|silicone|all||0.5|3
Petrolatum|Petroleum Jelly|Occlusive|Strong occlusive that seals in moisture.|0|1||dry;all||1|30
Mineral Oil|Paraffinum Liquidum|Occlusive;Emollient|Cosmetic-grade mineral oil seals in moisture.|0|1||dry;all||1|30
Butyrospermum Parkii Butter|Shea Butter|Emollient;Occlusive|Rich plant butter that softens and protects dry skin.|0|2||dry||1|20
Simmondsia Chinensis Seed Oil|Jojoba Oil|Emollient|Wax-ester oil similar to skin's own sebum.|0|2||all||1|10
Argania Spinosa Kernel Oil|Argan Oil|Emollient|Nourishing plant oil rich in fatty acids.|0|0||dry||1|10
Cocos Nucifera Oil|Coconut Oil|Emollient;Occlusive|Rich oil that can clog pores for some people.|1|4||dry||1|20
Helianthus Annuus Seed Oil|Sunflower Seed Oil|Emollient|Light oil rich in linoleic acid.|0|0||all;oily||1|10
Rosa Canina Fruit Oil|Rosehip Oil|Emollient;Antioxidant|Oil with natural fatty acids and a little provitamin A.|0|1||dry||0.5|5
Olea Europaea Fruit Oil|Olive Oil|Emollient|Rich oil that can feel heavy on oily skin.|1|2||dry||1|10
Prunus Amygdalus Dulcis Oil|Sweet Almond Oil|Emollient|Soft plant oil; avoid with nut allergy.|1|2|allergen|dry||1|10
Ricinus Communis Seed Oil|Castor Oil|Emollient;Film-former|Thick oil that adds gloss, common in lipsticks.|0|1||all||1|40
Isopropyl Myristate||Emollient;Solvent|Light emollient that spreads easily; can clog pores for acne-prone skin.|1|5||dry||1|10
Isopropyl Palmitate||Emollient|Light emollient with a silky feel.|1|4||dry||1|10
Ethylhexyl Palmitate||Emollient|Light, non-greasy emollient.|0|2||all||2|15
Dicaprylyl Carbonate||Emollient|Light plant-derived silicone alternative.|0|1||all||2|15
Triethylhexanoin||Emollient|Emollient that adds shine and spreadability.|0|1||all||2|15
Octyldodecanol||Emollient|Light fatty alcohol emollient.|0|1||all||1|10
Hydrogenated Polyisobutene||Emollient;Film-former|Gives gloss and slip, common in lip products.|0|1||all||5|40
Hydrogenated Polydecene||Emollient|Light, non-sticky emollient.|0|1||all||2|15
Diisostearyl Malate||Emollient|Thick, glossy emollient common in lipstick.|0|1||all||5|30
Cetyl Palmitate||Emollient;Thickener|Waxy ester that thickens and softens.|0|2||all||0.5|5
Lanolin|Wool Wax|Emollient;Occlusive|Rich, occlusive wax from sheep's wool; a known allergen for some.|2|0|allergen|dry||1|10
Cera Alba|Beeswax|Thickener;Film-former;Occlusive|Natural wax that thickens and protects.|1|2|allergen|all||1|15
Euphorbia Cerifera Wax|Candelilla Wax|Thickener;Film-former|Plant wax that gives structure to lip products.|0|1||all||1|15
Copernicia Cerifera Wax|Carnauba Wax|Thickener;Film-former|Hard plant wax that adds gloss and hold.|0|1||all||1|10
Ozokerite||Thickener|Mineral wax that gives stick products structure.|0|1||all||2|15
Tribehenin||Emollient;Thickener|Waxy ester that adds structure and slip.|0|1||all||1|10
Ceramide NP||Emollient;Skin-identical lipid|Skin-identical lipid that strengthens the moisture barrier.|0|0||dry;sensitive||0.01|1
Ceramide AP||Emollient;Skin-identical lipid|Skin-identical lipid that supports the barrier.|0|0||dry;sensitive||0.01|1
Ceramide EOP||Emollient;Skin-identical lipid|Barrier lipid that helps keep moisture in.|0|0||dry;sensitive||0.01|1
Cholesterol||Emollient;Skin-identical lipid|Barrier lipid that works with ceramides.|0|0||dry||0.1|2
Phytosphingosine||Skin-identical lipid;Soothing agent|Barrier lipid with mild calming properties.|0|0||all||0.05|0.5
Lecithin||Emulsifier;Emollient|Natural emulsifier that softens skin.|0|1||all||0.5|3
Tocopheryl Acetate|Vitamin E Acetate|Antioxidant;Emollient|Stable form of vitamin E that protects skin from oxidation.|0|2||all||0.1|1
Tocopherol|Vitamin E|Antioxidant|Antioxidant that also protects oils in the formula.|0|2||all||0.05|1
Ascorbic Acid|Vitamin C;L-Ascorbic Acid|Antioxidant;Brightening agent|Potent antioxidant that brightens; unstable and can sting.|3|0|sensitive_caution|normal;oily;combination|Retinol;Benzoyl Peroxide|5|20
Sodium Ascorbyl Phosphate||Antioxidant;Brightening agent|Gentler, more stable vitamin C that also suits acne-prone skin.|1|0||all;oily||1|5
Ascorbyl Glucoside||Antioxidant;Brightening agent|Stable vitamin C form that brightens gently.|1|0||all||2|10
Niacinamide|Vitamin B3;Nicotinamide|Brightening agent;Soothing agent|Evens tone, supports the barrier and reduces the look of pores.|1|0||all;oily;combination||2|10
Retinol|Vitamin A|Retinoid|Boosts renewal for smoother skin and fewer fine lines; can irritate.|4|0|pregnancy_caution;sensitive_caution|normal;oily;combination|Glycolic Acid;Salicylic Acid;Benzoyl Peroxide;Ascorbic Acid|0.01|1
Retinyl Palmitate||Retinoid|Mild, weaker vitamin A form.|2|0|pregnancy_caution|all|Benzoyl Peroxide|0.05|1
Bakuchiol||Retinoid;Antioxidant|Plant-based retinol alternative that is gentler.|1|0||all;sensitive||0.5|2
Glycolic Acid|AHA|Exfoliant|Small AHA that exfoliates and brightens; raises sun sensitivity.|4|0|sensitive_caution|normal;oily|Retinol;Benzoyl Peroxide|2|10
Lactic Acid|AHA|Exfoliant;Humectant|Gentler AHA that exfoliates and hydrates.|3|0|sensitive_caution|dry;normal|Retinol|2|10
Mandelic Acid|AHA|Exfoliant|Large-molecule AHA that is gentler on skin.|2|0||sensitive;normal|Retinol|2|10
Gluconolactone|PHA|Exfoliant;Humectant|Very gentle PHA that exfoliates and hydrates.|1|0||sensitive;dry||2|10
Salicylic Acid|BHA|Exfoliant|Oil-soluble BHA that clears pores and treats blackheads.|3|0|pregnancy_caution;sensitive_caution|oily;acne-prone|Retinol;Benzoyl Peroxide|0.5|2
Azelaic Acid||Brightening agent;Exfoliant;Soothing agent|Calms redness, evens tone and helps acne.|2|0||all;acne-prone;sensitive||5|20
Tranexamic Acid||Brightening agent|Helps fade stubborn dark spots.|1|0||all||2|5
Arbutin|Alpha-Arbutin|Brightening agent|Fades dark spots by slowing pigment production.|1|0||all||1|2
Kojic Acid||Brightening agent|Brightens dark spots; can sensitise skin.|3|0|sensitive_caution|normal;oily||1|2
Benzoyl Peroxide||Antibacterial;Exfoliant|Kills acne bacteria; drying and bleaches fabric.|4|0|sensitive_caution|oily;acne-prone|Retinol;Ascorbic Acid;Glycolic Acid|2.5|10
Zinc Oxide||UV filter;Soothing agent|Mineral sunscreen that blocks UVA and UVB and soothes.|0|1||all;sensitive||5|25
Titanium Dioxide||UV filter|Mineral UV filter, mainly UVB and short UVA.|0|1||all;sensitive||2|25
Butyl Methoxydibenzoylmethane|Avobenzone|UV filter|Chemical UVA filter; needs stabilising.|2|1|sensitive_caution|all||1|3
Octocrylene||UV filter|Chemical UV filter that also stabilises avobenzone.|2|1|allergen|all||2|10
Homosalate||UV filter|Chemical UVB filter.|1|1||all||3|10
Ethylhexyl Salicylate|Octisalate|UV filter|Chemical UVB filter.|1|1||all||2|5
Ethylhexyl Methoxycinnamate|Octinoxate|UV filter|Chemical UVB filter.|2|1|sensitive_caution|all||2|7.5
Bis-Ethylhexyloxyphenol Methoxyphenyl Triazine|Tinosorb S|UV filter|Photostable broad-spectrum chemical UV filter.|1|0||all||1|5
Diethylamino Hydroxybenzoyl Hexyl Benzoate|Uvinul A Plus|UV filter|Photostable UVA filter.|1|0||all||1|10
Centella Asiatica Extract|Cica;Gotu Kola|Soothing agent;Antioxidant|Calms redness and supports healing.|0|0||sensitive;all||0.1|2
Madecassoside||Soothing agent|Active from centella that calms irritated skin.|0|0||sensitive;all||0.1|1
Aloe Barbadensis Leaf Juice|Aloe Vera|Soothing agent;Humectant|Cooling, hydrating plant juice.|0|0||all;sensitive||1|50
Camellia Sinensis Leaf Extract|Green Tea Extract|Antioxidant;Soothing agent|Antioxidant that calms and protects.|0|0||all;oily||0.1|2
Glycyrrhiza Glabra Root Extract|Licorice Root Extract|Soothing agent;Brightening agent|Calms and gently brightens.|0|0||all||0.1|2
Bisabolol||Soothing agent|Chamomile-derived calming ingredient.|0|0||sensitive;all||0.1|1
Chamomilla Recutita Flower Extract|Chamomile Extract|Soothing agent|Calming extract; may bother people allergic to daisies.|1|0|allergen|sensitive||0.1|2
Avena Sativa Kernel Extract|Oat Extract|Soothing agent|Calms itch and dryness.|0|0||sensitive;dry||0.1|2
Resveratrol||Antioxidant|Antioxidant from grapes that protects skin.|0|0||all||0.1|1
Ferulic Acid||Antioxidant|Antioxidant that boosts the stability of vitamins C and E.|1|0||all||0.1|1
Ubiquinone|Coenzyme Q10|Antioxidant|Antioxidant that supports skin energy.|0|0||all||0.1|1
Caffeine||Antioxidant;Soothing agent|Helps reduce puffiness and protects skin.|0|0||all||0.5|3
Palmitoyl Tripeptide-1||Peptide|Signalling peptide used for firmer-looking skin.|0|0||all||0.0001|0.01
Palmitoyl Tetrapeptide-7||Peptide|Signalling peptide that helps calm and firm.|0|0||all||0.0001|0.01
Acetyl Hexapeptide-8|Argireline|Peptide|Peptide marketed to soften the look of expression lines.|0|0||all||0.01|0.1
Copper Tripeptide-1||Peptide|Copper peptide used for firmness and repair.|0|0||all||0.01|0.1
Sodium Lauryl Sulfate|SLS|Surfactant|Strong cleanser that foams a lot; can dry and irritate.|4|1|sulfate;sensitive_caution|oily||5|20
Sodium Laureth Sulfate|SLES|Surfactant|Foaming cleanser, milder than SLS.|3|1|sulfate;sensitive_caution|oily;normal||5|20
Cocamidopropyl Betaine||Surfactant|Mild foaming cleanser.|2|0|allergen|all||2|10
Decyl Glucoside||Surfactant|Very gentle sugar-based cleanser.|1|0||sensitive;all||2|10
Coco-Glucoside||Surfactant|Gentle coconut-derived cleanser.|1|0||sensitive;all||2|10
Sodium Cocoyl Isethionate||Surfactant|Mild, creamy cleanser.|1|0||dry;sensitive||2|15
Disodium Laureth Sulfosuccinate||Surfactant|Mild foaming cleanser.|1|0||sensitive;all||2|10
Cocamide MEA||Surfactant;Thickener|Foam booster and thickener.|2|0|allergen|all||1|5
Sodium Lauroyl Sarcosinate||Surfactant|Mild foaming cleanser.|2|0||all||2|10
Polysorbate 20||Emulsifier;Surfactant|Dissolves oils and fragrance in water.|1|0||all||0.5|5
Polysorbate 60||Emulsifier|Emulsifier for creams and lotions.|1|0||all||0.5|5
Glyceryl Stearate||Emulsifier;Emollient|Mild emulsifier that keeps oil and water mixed.|0|1||all||0.5|5
Glyceryl Stearate Citrate||Emulsifier|Natural-type emulsifier for creams.|0|1||all||0.5|5
PEG-100 Stearate||Emulsifier|Emulsifier that stabilises creams.|1|0||all||0.5|5
Ceteareth-20||Emulsifier|Strong emulsifier for lotions.|1|0||all||0.5|5
Sorbitan Olivate||Emulsifier|Plant-derived emulsifier.|0|0||all||0.5|3
Xanthan Gum||Thickener|Natural thickener that stabilises gels and creams.|0|0||all||0.1|1
Carbomer||Thickener|Gel-forming thickener.|0|0||all||0.1|1
Acrylates/C10-30 Alkyl Acrylate Crosspolymer||Thickener;Emulsifier|Thickens and stabilises emulsions.|0|0||all||0.05|0.5
Hydroxyethylcellulose||Thickener|Plant-based thickener.|0|0||all||0.1|1
Cellulose Gum||Thickener|Thickener that gives body.|0|0||all||0.1|2
Sodium Polyacrylate||Thickener|Synthetic thickener.|0|0||all||0.1|2
Silica||Thickener;Absorbent|Mattifying powder that absorbs oil.|0|0||oily||1|10
Magnesium Aluminum Silicate||Thickener|Clay-based thickener.|0|0||all||0.5|3
Disteardimonium Hectorite||Thickener|Clay thickener for oils and mascara.|0|0||all||1|5
Phenoxyethanol||Preservative|Common modern preservative that protects against microbes.|1|0||all||0.2|1
Ethylhexylglycerin||Preservative;Emollient|Boosts preservatives and softens skin.|1|0||all||0.1|1
Caprylyl Glycol||Preservative;Humectant|Boosts preservatives and hydrates.|0|0||all||0.3|1
Methylparaben||Preservative|Effective preservative; low reported risk at permitted levels.|1|0|paraben|all||0.1|0.4
Propylparaben||Preservative|Preservative; permitted at low limits.|1|0|paraben|all||0.05|0.14
Sodium Benzoate||Preservative|Preservative that works in acidic products.|1|0||all||0.1|0.5
Potassium Sorbate||Preservative|Mild preservative.|1|0||all||0.1|0.5
Benzyl Alcohol||Preservative;Solvent|Preservative and solvent; allergen at high levels.|2|0|allergen|all||0.2|1
Chlorphenesin||Preservative|Preservative that also fights fungi.|1|0||all||0.1|0.3
Methylisothiazolinone||Preservative|Effective preservative but a known allergen; avoid in leave-ons.|4|0|allergen;sensitive_caution|all||0.001|0.01
Dehydroacetic Acid||Preservative|Mild preservative, often with benzyl alcohol.|1|0||all||0.1|0.6
Disodium EDTA||Chelating agent|Locks metal ions to keep products stable.|1|0||all||0.05|0.2
Parfum|Fragrance;Perfume|Fragrance|Scent blend; a leading cause of cosmetic allergy.|3|0|fragrance;allergen;sensitive_caution|normal||0.1|1
Linalool||Fragrance|Scent ingredient that can sensitise after oxidising.|3|0|fragrance;allergen;sensitive_caution|normal||0.01|0.5
Limonene||Fragrance|Citrus scent ingredient; can sensitise after oxidising.|3|0|fragrance;allergen;sensitive_caution|normal||0.01|0.5
Citronellol||Fragrance|Rose-like scent that can cause allergy.|3|0|fragrance;allergen;sensitive_caution|normal||0.01|0.5
Geraniol||Fragrance|Floral scent ingredient that can cause allergy.|3|0|fragrance;allergen;sensitive_caution|normal||0.01|0.5
Lavandula Angustifolia Oil|Lavender Oil|Fragrance|Essential oil that can irritate or sensitise.|3|0|essential_oil;fragrance;allergen;sensitive_caution|normal||0.05|1
Mentha Piperita Oil|Peppermint Oil|Fragrance|Cooling essential oil that can irritate.|3|0|essential_oil;fragrance;sensitive_caution|normal||0.05|1
Citrus Limon Peel Oil|Lemon Peel Oil|Fragrance|Citrus oil that raises sun sensitivity.|3|0|essential_oil;fragrance;allergen;sensitive_caution|normal||0.05|1
Eucalyptus Globulus Leaf Oil|Eucalyptus Oil|Fragrance|Cooling essential oil that can irritate.|3|0|essential_oil;fragrance;sensitive_caution|normal||0.05|1
Melaleuca Alternifolia Leaf Oil|Tea Tree Oil|Antibacterial;Fragrance|Essential oil used for blemishes; can sensitise.|3|0|essential_oil;allergen;sensitive_caution|oily;acne-prone||0.1|5
Alcohol Denat.|Denatured Alcohol;SD Alcohol|Solvent|Drying alcohol that evaporates quickly and can irritate.|3|0|drying_alcohol;sensitive_caution|oily||1|40
Isododecane||Solvent|Light volatile solvent used in long-wear makeup.|0|1||all||2|30
Citric Acid||pH adjuster;Chelating agent|Adjusts pH to keep products stable.|1|0||all||0.01|1
Sodium Hydroxide||pH adjuster|Raises pH; used in tiny amounts.|1|0||all||0.01|0.5
Sodium Citrate||pH adjuster|Buffer that helps hold pH steady.|0|0||all||0.05|1
Triethanolamine||pH adjuster|Raises pH of carbomer gels.|1|0|sensitive_caution|all||0.1|1
Tromethamine||pH adjuster|Raises pH of gels.|1|0||all||0.1|1
Acrylates Copolymer||Film-former|Forms a flexible film on skin or lashes.|0|0||all||1|10
VP/Eicosene Copolymer||Film-former|Water-resistant film former.|0|0||all||0.5|5
Trimethylsiloxysilicate||Film-former|Long-wear silicone film former.|0|1|silicone|all||1|10
Pullulan||Film-former|Plant-derived film former for a tightening feel.|0|0||all||0.5|3
Acacia Senegal Gum||Film-former;Thickener|Natural gum that helps lash products hold.|0|0||all||1|5
Polyethylene||Thickener;Exfoliant|Plastic beads or wax used to texturise; avoid as scrub beads.|0|0||all||1|10
Nylon-12||Absorbent;Film-former|Fine powder for a soft-focus finish.|0|0||all||1|10
Polymethylsilsesquioxane||Absorbent|Powder that gives a smooth, matte feel.|0|0||all||1|10
Silica Dimethyl Silylate||Absorbent|Powder that adds slip and mattifies.|0|0||oily||1|5
Synthetic Fluorphlogopite||Colorant/Pigment|Synthetic mica that adds shimmer and a smooth feel.|0|0||all||5|30
Mica||Colorant/Pigment|Shimmery mineral powder.|0|0||all||2|30
Talc||Absorbent|Soft mineral powder that absorbs oil.|0|0||oily||2|30
Kaolin||Absorbent;Soothing agent|Clay that absorbs oil.|1|0||oily||1|20
Bentonite||Absorbent|Clay that absorbs oil.|1|0||oily||1|10
Charcoal Powder||Absorbent|Absorbs oil and impurities.|0|0||oily||0.5|5
Sodium Chloride|Salt|Thickener|Thickens surfactant cleansers.|1|0||all||0.5|3
CI 77891|Titanium Dioxide (pigment)|Colorant/Pigment|White pigment that adds opacity.|0|0||all||0.5|15
CI 77491|Red Iron Oxide|Colorant/Pigment|Red-brown mineral pigment.|0|0||all||0.1|10
CI 77492|Yellow Iron Oxide|Colorant/Pigment|Yellow mineral pigment.|0|0||all||0.1|10
CI 77499|Black Iron Oxide|Colorant/Pigment|Black mineral pigment.|0|0||all||0.5|15
CI 15850|Red 7;Lake Red 6|Colorant/Pigment|Red colourant for lipsticks.|0|0||all||0.5|5
CI 45410|Red 27;Red 28|Colorant/Pigment|Bright pink-red colourant for lipsticks.|0|0||all||0.1|3
CI 19140|Yellow 5|Colorant/Pigment|Yellow dye; may trigger allergy in sensitive people.|1|0|allergen|all||0.1|2
CI 75470|Carmine|Colorant/Pigment|Natural red pigment from insects; not vegan.|1|0|allergen|all||0.1|5
Behentrimonium Chloride||Surfactant;Conditioning agent|Conditioning agent that detangles hair.|2|0||all||1|5
Cetrimonium Chloride||Surfactant;Conditioning agent|Conditioning agent for hair.|2|0||all||0.5|3
Hydrolyzed Keratin||Conditioning agent|Protein that coats and conditions hair.|0|0||all||0.1|2
Biotin|Vitamin B7|Conditioning agent|Vitamin used in hair products; limited evidence from topical use.|0|0||all||0.01|0.5
Zinc Pyrithione||Antibacterial|Anti-dandruff active.|2|0||oily||0.5|2
Climbazole||Antibacterial|Anti-dandruff antifungal active.|2|0||oily||0.5|0.5
Hydrogenated Castor Oil||Thickener;Emollient|Hardened oil that thickens balms and sticks.|0|1||all||1|10
Zinc PCA||Humectant;Antibacterial|Helps balance oil and hydrate.|0|0||oily||0.1|1
Dimethiconol||Emollient;Film-former|Conditioning silicone for hair and skin.|0|1|silicone|all||0.5|5
"""

CATEGORIES = [
    ("Humectant", "Attracts moisture"),
    ("Emollient", "Softens and smooths skin"),
    ("Occlusive", "Seals in moisture"),
    ("Emulsifier", "Keeps oil and water mixed"),
    ("Surfactant", "Cleanses"),
    ("Preservative", "Prevents microbial growth"),
    ("Exfoliant", "Sheds dead skin cells (AHA/BHA/PHA)"),
    ("Retinoid", "Vitamin A family; boosts skin renewal"),
    ("Antioxidant", "Protects against free-radical damage"),
    ("Brightening agent", "Evens tone and fades dark spots"),
    ("Soothing agent", "Calms redness and irritation"),
    ("Peptide", "Signalling amino-acid chains"),
    ("UV filter", "Absorbs or blocks UV light"),
    ("Colorant/Pigment", "Adds colour"),
    ("Fragrance", "Adds scent"),
    ("Solvent", "Dissolves other ingredients"),
    ("Thickener", "Gives body and texture"),
    ("Film-former", "Forms a flexible film on skin or lashes"),
    ("pH adjuster", "Controls acidity"),
    ("Skin-identical lipid", "Replenishes natural skin lipids"),
    ("Antibacterial", "Reduces bacteria or fungi"),
    ("Absorbent", "Absorbs oil and adds a matte feel"),
    ("Chelating agent", "Binds metal ions for stability"),
    ("Conditioning agent", "Conditions hair"),
]


def parse():
    """Turn RAW into a list of dicts. Raises on malformed lines (checked by tests)."""
    items = []
    for line in RAW.strip().splitlines():
        parts = line.split("|")
        if len(parts) != 11:
            raise ValueError(f"Bad ingredient line ({len(parts)} fields): {line[:60]}")
        inci, aliases, cats, desc, irr, com, flags, skin, incompat, mn, mx = parts
        items.append({
            "inci_name": inci.strip(),
            "aliases": [a.strip() for a in aliases.split(";") if a.strip()],
            "categories": [c.strip() for c in cats.split(";") if c.strip()],
            "description": desc.strip(),
            "irritancy": int(irr),
            "comedogenic": int(com),
            "flags": [f.strip() for f in flags.split(";") if f.strip()],
            "skin_types": [s.strip() for s in skin.split(";") if s.strip()],
            "incompatible_with": [i.strip() for i in incompat.split(";") if i.strip()],
            "typical_min": float(mn) if mn else None,
            "typical_max": float(mx) if mx else None,
            "range_source": RANGE_SOURCE,
        })
    return items

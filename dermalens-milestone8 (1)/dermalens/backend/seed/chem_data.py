"""Chemistry data for DermaLens ingredients.

STRUCTURES  one line per ingredient that is a single, defined molecule (or a typical representative):
    INCI name | SMILES (Kekule form) | formula (typed separately, as a cross-check) | CAS | dissolves in | note
The formula is typed independently of the SMILES; the tests compute the formula from the SMILES and
fail if they disagree, which catches typing mistakes. CAS numbers are checked with the CAS check digit.
These entries were written by the DermaLens author from standard chemistry references and have NOT been
cross-checked against PubChem here: always verify before relying on them.

NO_STRUCTURE  ingredients that have no single drawable structure (mixtures, polymers, minerals, big molecules):
    INCI name | kind | explanation | formula text (optional, idealised, not calculated)
"""

STRUCTURES = """
Water|O|H2O|7732-18-5|water|
Glycerin|OCC(O)CO|C3H8O3|56-81-5|water|
Butylene Glycol|CC(O)CCO|C4H10O2|107-88-0|water|1,3-butanediol
Propylene Glycol|CC(O)CO|C3H8O2|57-55-6|water|
Propanediol|OCCCO|C3H8O2|504-63-2|water|1,3-propanediol
Pentylene Glycol|CCCC(O)CO|C5H12O2|5343-92-0|water and oil|1,2-pentanediol
Panthenol|CC(C)(CO)C(O)C(=O)NCCCO|C9H19NO4|81-13-0|water|
Urea|NC(=O)N|CH4N2O|57-13-6|water|
Sodium PCA|[Na+].[O-]C(=O)C1CCC(=O)N1|C5H6NNaO3|28874-51-3|water|sodium salt of pyroglutamic acid
Sorbitol|OCC(O)C(O)C(O)C(O)CO|C6H14O6|50-70-4|water|
Betaine|C[N+](C)(C)CC([O-])=O|C5H11NO2|107-43-7|water|
Allantoin|O=C1NC(NC(N)=O)C(=O)N1|C4H6N4O3|97-59-6|water (slightly)|
Squalane|CC(C)CCCC(C)CCCC(C)CCCCC(C)CCCC(C)CCCC(C)C|C30H62|111-01-3|oil|
Cetyl Alcohol|CCCCCCCCCCCCCCCCO|C16H34O|36653-82-4|oil|
Stearyl Alcohol|CCCCCCCCCCCCCCCCCCO|C18H38O|112-92-5|oil|
Stearic Acid|CCCCCCCCCCCCCCCCCC(O)=O|C18H36O2|57-11-4|oil|
Cyclopentasiloxane|C[Si]1(C)O[Si](C)(C)O[Si](C)(C)O[Si](C)(C)O[Si](C)(C)O1|C10H30O5Si5|541-02-6|oil (silicone)|
Isopropyl Myristate|CCCCCCCCCCCCCC(=O)OC(C)C|C17H34O2|110-27-0|oil|
Isopropyl Palmitate|CCCCCCCCCCCCCCCC(=O)OC(C)C|C19H38O2|142-91-6|oil|
Ethylhexyl Palmitate|CCCCCCCCCCCCCCCC(=O)OCC(CC)CCCC|C24H48O2|29806-73-3|oil|
Dicaprylyl Carbonate|CCCCCCCCOC(=O)OCCCCCCCC|C17H34O3|1680-31-5|oil|
Triethylhexanoin|CCCCC(CC)C(=O)OCC(OC(=O)C(CC)CCCC)COC(=O)C(CC)CCCC|C27H50O6|7360-38-5|oil|
Octyldodecanol|OCC(CCCCCCCC)CCCCCCCCCC|C20H42O|5333-42-6|oil|
Cetyl Palmitate|CCCCCCCCCCCCCCCC(=O)OCCCCCCCCCCCCCCCC|C32H64O2|540-10-3|oil (wax-like solid)|
Tribehenin|CCCCCCCCCCCCCCCCCCCCCC(=O)OCC(OC(=O)CCCCCCCCCCCCCCCCCCCCC)COC(=O)CCCCCCCCCCCCCCCCCCCCC|C69H134O6|18641-57-1|oil (waxy solid)|
Cholesterol|CC(C)CCCC(C)C1CCC2C1(CCC3C2CC=C4C3(CCC(C4)O)C)C|C27H46O|57-88-5|oil|
Phytosphingosine|NC(CO)C(O)C(O)CCCCCCCCCCCCCC|C18H39NO3|554-62-1|oil|
Ceramide NP|CCCCCCCCCCCCCCCCCC(=O)NC(CO)C(O)C(O)CCCCCCCCCCCCCC|C36H73NO4|100403-19-8|oil|N-stearoyl phytosphingosine
Tocopheryl Acetate|CC1=C(C)C2=C(CCC(C)(CCCC(C)CCCC(C)CCCC(C)C)O2)C(C)=C1OC(C)=O|C31H52O3|7695-91-2|oil|
Tocopherol|CC1=C(C)C2=C(CCC(C)(CCCC(C)CCCC(C)CCCC(C)C)O2)C(C)=C1O|C29H50O2|10191-41-0|oil|vitamin E (alpha form)
Ascorbic Acid|OCC(O)C1OC(=O)C(O)=C1O|C6H8O6|50-81-7|water|vitamin C
Sodium Ascorbyl Phosphate|[Na+].[Na+].[Na+].OCC(O)C1OC(=O)C(OP([O-])([O-])=O)=C1[O-]|C6H6Na3O9P|66170-10-3|water|the exact charge position on the ring is simplified
Ascorbyl Glucoside|OCC1OC(OC2=C(O)C(=O)OC2C(O)CO)C(O)C(O)C1O|C12H18O11|129499-78-1|water|
Niacinamide|NC(=O)C1=CN=CC=C1|C6H6N2O|98-92-0|water|vitamin B3
Retinol|CC1=C(C(CCC1)(C)C)C=CC(=CC=CC(=CCO)C)C|C20H30O|68-26-8|oil|vitamin A
Retinyl Palmitate|CCCCCCCCCCCCCCCC(=O)OCC=C(C)C=CC=C(C)C=CC1=C(C)CCCC1(C)C|C36H60O2|79-81-2|oil|
Bakuchiol|CC(C)=CCCC(C)(C=C)C=CC1=CC=C(O)C=C1|C18H24O|10309-37-2|oil|
Glycolic Acid|OCC(O)=O|C2H4O3|79-14-1|water|
Lactic Acid|CC(O)C(O)=O|C3H6O3|50-21-5|water|
Mandelic Acid|OC(C1=CC=CC=C1)C(O)=O|C8H8O3|90-64-2|water|
Gluconolactone|OCC1OC(=O)C(O)C(O)C1O|C6H10O6|90-80-2|water|
Salicylic Acid|OC(=O)C1=CC=CC=C1O|C7H6O3|69-72-7|oil and alcohol|
Azelaic Acid|OC(=O)CCCCCCCC(O)=O|C9H16O4|123-99-9|water (slightly)|
Tranexamic Acid|NCC1CCC(CC1)C(O)=O|C8H15NO2|1197-18-8|water|
Arbutin|OCC1OC(OC2=CC=C(O)C=C2)C(O)C(O)C1O|C12H16O7|497-76-7|water|
Kojic Acid|OCC1=CC(=O)C(O)=CO1|C6H6O4|501-30-4|water|
Benzoyl Peroxide|O=C(OOC(=O)C1=CC=CC=C1)C1=CC=CC=C1|C14H10O4|94-36-0|oil (poorly in water)|
Zinc Oxide|O=[Zn]|ZnO|1314-13-2|neither (insoluble powder)|written as a formula unit; the real solid is a crystal lattice
Titanium Dioxide|O=[Ti]=O|TiO2|13463-67-7|neither (insoluble powder)|written as a formula unit; the real solid is a crystal lattice
Butyl Methoxydibenzoylmethane|COC1=CC=C(C=C1)C(=O)CC(=O)C1=CC=C(C=C1)C(C)(C)C|C20H22O3|70356-09-1|oil|avobenzone
Octocrylene|CCCCC(CC)COC(=O)C(C#N)=C(C1=CC=CC=C1)C1=CC=CC=C1|C24H27NO2|6197-30-4|oil|
Homosalate|CC1CC(CC(C)(C1)C)OC(=O)C1=CC=CC=C1O|C16H22O3|118-56-9|oil|
Ethylhexyl Salicylate|CCCCC(CC)COC(=O)C1=CC=CC=C1O|C15H22O3|118-60-5|oil|
Ethylhexyl Methoxycinnamate|CCCCC(CC)COC(=O)C=CC1=CC=C(OC)C=C1|C18H26O3|5466-77-3|oil|octinoxate
Bis-Ethylhexyloxyphenol Methoxyphenyl Triazine|COC1=CC=C(C=C1)C1=NC(=NC(=N1)C1=CC=C(OCC(CC)CCCC)C=C1O)C1=CC=C(OCC(CC)CCCC)C=C1O|C38H49N3O5|187393-00-6|oil|bemotrizinol
Diethylamino Hydroxybenzoyl Hexyl Benzoate|CCCCCCOC(=O)C1=CC=CC=C1C(=O)C1=CC=C(N(CC)CC)C=C1O|C24H31NO4|302776-68-7|oil|
Bisabolol|CC1=CCC(CC1)(C(C)CCC=C(C)C)O|C15H26O|515-69-5|oil|alpha-bisabolol
Resveratrol|OC1=CC=C(C=CC2=CC(O)=CC(O)=C2)C=C1|C14H12O3|501-36-0|alcohol and oil|
Ferulic Acid|COC1=CC(C=CC(O)=O)=CC=C1O|C10H10O4|1135-24-6|alcohol (slightly in water)|
Ubiquinone|COC1=C(OC)C(=O)C(C)=C(C1=O)CC=C(C)CCC=C(C)CCC=C(C)CCC=C(C)CCC=C(C)CCC=C(C)CCC=C(C)CCC=C(C)CCC=C(C)CCC=C(C)C|C59H90O4|303-98-0|oil|coenzyme Q10
Caffeine|CN1C=NC2=C1C(=O)N(C)C(=O)N2C|C8H10N4O2|58-08-2|water (warm)|
Sodium Lauryl Sulfate|CCCCCCCCCCCCOS([O-])(=O)=O.[Na+]|C12H25NaO4S|151-21-3|water|
Cocamidopropyl Betaine|CCCCCCCCCCCC(=O)NCCC[N+](C)(C)CC([O-])=O|C19H38N2O3|||representative: the lauryl (C12) member of a mixture of coconut-derived chain lengths
Decyl Glucoside|CCCCCCCCCCOC1OC(CO)C(O)C(O)C1O|C16H32O6|54549-25-6|water|
Sodium Cocoyl Isethionate|CCCCCCCCCCCC(=O)OCCS([O-])(=O)=O.[Na+]|C14H27NaO5S|||representative: the lauroyl (C12) member of a mixture of coconut-derived chain lengths
Cocamide MEA|CCCCCCCCCCCC(=O)NCCO|C14H29NO2|||representative: the lauramide (C12) member of a mixture of coconut-derived chain lengths
Sodium Lauroyl Sarcosinate|CCCCCCCCCCCC(=O)N(C)CC([O-])=O.[Na+]|C15H28NNaO3|137-16-6|water|
Glyceryl Stearate|CCCCCCCCCCCCCCCCCC(=O)OCC(O)CO|C21H42O4|31566-31-1|oil|representative: the mono-ester; commercial grades also contain di-esters
Silica|O=[Si]=O|SiO2|7631-86-9|neither (insoluble powder)|written as a formula unit; the real material is a network solid
Phenoxyethanol|OCCOC1=CC=CC=C1|C8H10O2|122-99-6|water (slightly) and oil|
Ethylhexylglycerin|CCCCC(CC)COCC(O)CO|C11H24O3|70445-33-9|oil|
Caprylyl Glycol|CCCCCCC(O)CO|C8H18O2|1117-86-8|water (slightly) and oil|
Methylparaben|COC(=O)C1=CC=C(O)C=C1|C8H8O3|99-76-3|water (slightly) and oil|
Propylparaben|CCCOC(=O)C1=CC=C(O)C=C1|C10H12O3|94-13-3|oil (poorly in water)|
Sodium Benzoate|[Na+].[O-]C(=O)C1=CC=CC=C1|C7H5NaO2|532-32-1|water|
Potassium Sorbate|[K+].CC=CC=CC([O-])=O|C6H7KO2|24634-61-5|water|
Benzyl Alcohol|OCC1=CC=CC=C1|C7H8O|100-51-6|water (slightly) and oil|
Chlorphenesin|OCC(O)COC1=CC=C(Cl)C=C1|C9H11ClO3|104-29-0|water (slightly) and oil|
Methylisothiazolinone|CN1SC=CC1=O|C4H5NOS|2682-20-4|water|
Dehydroacetic Acid|CC(=O)C1C(=O)OC(C)=CC1=O|C8H8O4|520-45-6|oil (poorly in water)|
Disodium EDTA|[Na+].[Na+].OC(=O)CN(CCN(CC(O)=O)CC([O-])=O)CC([O-])=O|C10H14N2Na2O8|139-33-3|water|
Linalool|CC(C)=CCCC(C)(O)C=C|C10H18O|78-70-6|oil|
Limonene|CC(=C)C1CCC(C)=CC1|C10H16|138-86-3|oil|
Citronellol|CC(CCO)CCC=C(C)C|C10H20O|106-22-9|oil|
Geraniol|CC(C)=CCCC(C)=CCO|C10H18O|106-24-1|oil|
Alcohol Denat.|CCO|C2H6O|64-17-5|water and oil|ethanol (the "denatured" part is a small amount of added bittering agent)
Isododecane|CC(C)(C)CC(C)CC(C)(C)C|C12H26|31807-55-3|oil|
Citric Acid|OC(=O)CC(O)(CC(O)=O)C(O)=O|C6H8O7|77-92-9|water|
Sodium Hydroxide|[Na+].[OH-]|NaOH|1310-73-2|water|
Sodium Citrate|[Na+].[Na+].[Na+].OC(CC([O-])=O)(CC([O-])=O)C([O-])=O|C6H5Na3O7|68-04-2|water|trisodium citrate
Triethanolamine|OCCN(CCO)CCO|C6H15NO3|102-71-6|water|
Tromethamine|NC(CO)(CO)CO|C4H11NO3|77-86-1|water|
Sodium Chloride|[Na+].[Cl-]|NaCl|7647-14-5|water|
CI 77891|O=[Ti]=O|TiO2|13463-67-7|neither (insoluble powder)|the white pigment titanium dioxide
Behentrimonium Chloride|CCCCCCCCCCCCCCCCCCCCCC[N+](C)(C)C.[Cl-]|C25H54ClN|17301-53-0|water (dispersible)|
Cetrimonium Chloride|CCCCCCCCCCCCCCCC[N+](C)(C)C.[Cl-]|C19H42ClN|112-02-7|water|
Biotin|OC(=O)CCCCC1SCC2NC(=O)NC12|C10H16N2O3S|58-85-5|water (slightly)|vitamin B7
Zinc Pyrithione|[Zn+2].[O-]N1C=CC=CC1=S.[O-]N1C=CC=CC1=S|C10H8N2O2S2Zn|13463-41-7|neither (insoluble powder)|drawn as separate ions; the real compound is a zinc complex
Climbazole|CC(C)(C)C(=O)C(OC1=CC=C(Cl)C=C1)N1C=CN=C1|C15H17ClN2O2|38083-17-9|oil|
Zinc PCA|[Zn+2].[O-]C(=O)C1CCC(=O)N1.[O-]C(=O)C1CCC(=O)N1|C10H12N2O6Zn|15454-75-8|water|
"""

NO_STRUCTURE = """
Sodium Hyaluronate|polymer|A very long chain (often hundreds of thousands of Da) that repeats a sugar pair, glucuronic acid and N-acetylglucosamine. Because of its size it stays on the skin surface and holds water there.|(C14H20NNaO11)n
Caprylic/Capric Triglyceride|mixture|A mixture of glycerol esters of caprylic (C8) and capric (C10) fatty acids. Each product is a blend, so there is no single structure.|
Cetearyl Alcohol|mixture|A blend of two fatty alcohols, cetyl (C16) and stearyl (C18). See those two entries for the structures.|
Dimethicone|polymer|A silicone polymer: a chain of repeating -Si(CH3)2-O- units. The chain length sets the thickness (viscosity).|(C2H6OSi)n
Phenyl Trimethicone|polymer|A short silicone chain with phenyl (benzene ring) groups attached. It is a polymer, so there is no single structure.|
Amodimethicone|polymer|A silicone polymer with amino side groups that bind to hair. No single structure.|
Petrolatum|mixture|A semi-solid mixture of long-chain hydrocarbons from petroleum. No single structure.|
Mineral Oil|mixture|A mixture of liquid hydrocarbons (alkanes) from petroleum. No single structure.|
Butyrospermum Parkii Butter|mixture|Shea butter: a natural fat made mostly of triglycerides of stearic and oleic acid. The exact make-up varies by batch.|
Simmondsia Chinensis Seed Oil|mixture|Jojoba oil is really a liquid wax: long-chain wax esters, not triglycerides. Composition varies.|
Argania Spinosa Kernel Oil|mixture|Argan oil: a natural oil of triglycerides rich in oleic and linoleic acid, with vitamin E. Composition varies.|
Cocos Nucifera Oil|mixture|Coconut oil: a natural fat of triglycerides, mostly lauric and myristic acid. Composition varies.|
Helianthus Annuus Seed Oil|mixture|Sunflower oil: a natural oil of triglycerides rich in linoleic acid. Composition varies.|
Rosa Canina Fruit Oil|mixture|Rosehip oil: a natural oil of triglycerides rich in linoleic and linolenic acid. Composition varies.|
Olea Europaea Fruit Oil|mixture|Olive oil: a natural oil of triglycerides, mostly oleic acid. Composition varies.|
Prunus Amygdalus Dulcis Oil|mixture|Sweet almond oil: a natural oil of triglycerides, mostly oleic acid. Composition varies.|
Ricinus Communis Seed Oil|mixture|Castor oil: triglycerides that are mostly ricinoleic acid, a fatty acid with an -OH group. Composition varies.|
Hydrogenated Polyisobutene|polymer|A saturated hydrocarbon polymer made from isobutene units. No single structure.|
Hydrogenated Polydecene|mixture|A mixture of saturated hydrocarbon oligomers made from decene. No single structure.|
Diisostearyl Malate|mixture|A diester of malic acid with isostearyl alcohol, which is itself a mixture of branched C18 isomers. No single structure.|
Lanolin|mixture|A natural wax from sheep wool: a very complex mixture of fatty-acid esters, alcohols and sterols.|
Cera Alba|mixture|Beeswax: a natural mixture of wax esters, hydrocarbons and free fatty acids.|
Euphorbia Cerifera Wax|mixture|Candelilla wax: a natural mixture of hydrocarbons, esters and free acids.|
Copernicia Cerifera Wax|mixture|Carnauba wax: a natural mixture dominated by wax esters of long-chain acids and alcohols.|
Ozokerite|mixture|A natural mineral wax made of long-chain hydrocarbons.|
Ceramide AP|complex|A ceramide: a fatty acid joined by an amide bond to phytosphingosine. The fatty acid part is alpha-hydroxylated, and commercial products vary. See Ceramide NP and Phytosphingosine for the core structure.|
Ceramide EOP|complex|An acylceramide with a very long fatty acid that is itself esterified to linoleic acid. A large lipid; no single standard drawing is used here.|
Lecithin|mixture|A natural mixture of phospholipids, mainly phosphatidylcholine. Fatty-acid chains differ from molecule to molecule.|
Centella Asiatica Extract|extract|A plant extract. Its actives (asiaticoside, madecassoside, asiatic and madecassic acid) are in a mixture with many other plant compounds.|
Madecassoside|complex|A large triterpene glycoside (about C48H78O20, 975 Da) from Centella. It is too large and complex to draw reliably here.|C48H78O20
Aloe Barbadensis Leaf Juice|extract|The gel of the aloe leaf: mostly water with polysaccharides, sugars and many minor compounds.|
Camellia Sinensis Leaf Extract|extract|Green tea extract. Its main actives are catechins such as EGCG, in a mixture.|
Glycyrrhiza Glabra Root Extract|extract|Licorice root extract. Actives such as glabridin and glycyrrhizin sit in a mixture.|
Chamomilla Recutita Flower Extract|extract|Chamomile extract: a mixture that includes bisabolol and apigenin among others.|
Avena Sativa Kernel Extract|extract|Oat extract: a mixture of beta-glucan, proteins, lipids and avenanthramides.|
Palmitoyl Tripeptide-1|peptide|A palmitic acid chain attached to the three-amino-acid peptide glycine-histidine-lysine (Gly-His-Lys). Peptides are drawn as a sequence here, not as atoms.|
Palmitoyl Tetrapeptide-7|peptide|A palmitic acid chain attached to the four-amino-acid peptide Gly-Gln-Pro-Arg. Peptides are drawn as a sequence here, not as atoms.|
Acetyl Hexapeptide-8|peptide|An acetylated six-amino-acid peptide: Glu-Glu-Met-Gln-Arg-Arg. Peptides are drawn as a sequence here, not as atoms.|
Copper Tripeptide-1|peptide|The peptide glycine-histidine-lysine (Gly-His-Lys) bound to a copper(II) ion. Peptides are drawn as a sequence here, not as atoms.|
Sodium Laureth Sulfate|mixture|A lauryl alcohol that has been ethoxylated (about 1 to 3 ethylene-oxide units) and then sulfated. The number of units varies, so there is no single structure.|
Coco-Glucoside|mixture|A mixture of sugar glucosides of coconut-derived fatty alcohols (C8 to C16). See Decyl Glucoside for a typical member.|
Disodium Laureth Sulfosuccinate|mixture|An ethoxylated lauryl alcohol esterified with sulfosuccinic acid. The ethoxylation number varies.|
Polysorbate 20|mixture|Sorbitan with about 20 ethylene-oxide units and one lauric acid. The ethoxylation is an average, so there is no single structure.|
Polysorbate 60|mixture|Sorbitan with about 20 ethylene-oxide units and one stearic acid. The ethoxylation is an average, so there is no single structure.|
Glyceryl Stearate Citrate|mixture|A blend of glyceryl stearate esterified with citric acid. No single structure.|
PEG-100 Stearate|polymer|Stearic acid joined to a polyethylene glycol chain of about 100 ethylene-oxide units. The chain length is an average.|
Ceteareth-20|mixture|Cetearyl alcohol with about 20 ethylene-oxide units attached. The number is an average.|
Sorbitan Olivate|mixture|Esters of sorbitan with fatty acids from olive oil. A mixture.|
Xanthan Gum|polymer|A bacterial polysaccharide, a very large chain built from repeating glucose, mannose and glucuronic-acid units.|
Carbomer|polymer|A cross-linked polymer of acrylic acid. It swells in water to form a gel. No single structure.|
Acrylates/C10-30 Alkyl Acrylate Crosspolymer|polymer|A cross-linked polymer of acrylic acid and long-chain alkyl acrylate. No single structure.|
Hydroxyethylcellulose|polymer|Cellulose (a glucose polymer) that has been modified with -CH2CH2OH groups.|
Cellulose Gum|polymer|Sodium carboxymethylcellulose: cellulose with -CH2COONa groups added.|
Sodium Polyacrylate|polymer|A polymer made of repeating sodium acrylate units, -CH2-CH(COONa)-.|(C3H3NaO2)n
Magnesium Aluminum Silicate|mineral|A natural clay (smectite): layered magnesium aluminium silicate. Not a single molecule.|
Disteardimonium Hectorite|mineral|A clay (hectorite) that has been treated with a long-chain ammonium compound so it disperses in oil. Not a single molecule.|
Parfum|mixture|Fragrance is a blend of many aroma chemicals whose make-up is a trade secret. It cannot have one structure. Known allergens in it (such as linalool) are listed separately.|
Lavandula Angustifolia Oil|mixture|Lavender essential oil: mostly linalool and linalyl acetate, with many minor compounds.|
Mentha Piperita Oil|mixture|Peppermint essential oil: mostly menthol and menthone.|
Citrus Limon Peel Oil|mixture|Lemon peel essential oil: mostly limonene.|
Eucalyptus Globulus Leaf Oil|mixture|Eucalyptus essential oil: mostly 1,8-cineole (eucalyptol).|
Melaleuca Alternifolia Leaf Oil|mixture|Tea tree essential oil: mostly terpinen-4-ol and gamma-terpinene.|
Acrylates Copolymer|polymer|A copolymer of acrylic acid and its esters. No single structure.|
VP/Eicosene Copolymer|polymer|A copolymer of vinylpyrrolidone and a long-chain alkene (eicosene).|
Trimethylsiloxysilicate|polymer|A resin-like silicone made of branched Si-O units capped with -Si(CH3)3 groups.|
Pullulan|polymer|A polysaccharide made by a fungus: repeating maltotriose (three glucose) units.|
Acacia Senegal Gum|polymer|Gum arabic: a natural mixture of large polysaccharide-protein complexes.|
Polyethylene|polymer|A long chain that repeats -CH2-CH2-. Used here as tiny beads or powder.|(C2H4)n
Nylon-12|polymer|A polyamide made from laurolactam: repeating -NH-(CH2)11-CO- units.|(C12H23NO)n
Polymethylsilsesquioxane|polymer|A cross-linked silicone resin powder with the unit CH3-SiO1.5.|
Silica Dimethyl Silylate|polymer|Silica particles whose surface has been treated with dimethylsilyl groups.|
Synthetic Fluorphlogopite|mineral|A man-made mica: a layered potassium magnesium aluminosilicate containing fluorine.|KMg3(AlSi3O10)F2
Mica|mineral|A natural layered potassium aluminium silicate mineral. Not a single molecule.|KAl2(AlSi3O10)(OH)2
Talc|mineral|A natural layered magnesium silicate mineral. Not a single molecule.|Mg3Si4O10(OH)2
Kaolin|mineral|A natural clay mineral, aluminium silicate hydroxide.|Al2Si2O5(OH)4
Bentonite|mineral|A natural clay made mostly of montmorillonite. Not a single molecule.|
Charcoal Powder|mineral|Activated carbon: a porous form of carbon with no molecular structure to draw.|C
CI 77491|mineral|Red iron oxide pigment (iron(III) oxide). A crystalline solid, not a molecule.|Fe2O3
CI 77492|mineral|Yellow iron oxide pigment (hydrated iron(III) oxide-hydroxide). A crystalline solid.|FeO(OH)
CI 77499|mineral|Black iron oxide pigment (mixed iron(II,III) oxide, magnetite). A crystalline solid.|Fe3O4
CI 15850|complex|An azo dye (D&C Red 7 type) used as a calcium lake pigment. A coloured organic salt; not drawn here.|
CI 45410|complex|A xanthene dye (a halogenated fluorescein, D&C Red 27 type). A large halogenated dye; not drawn here.|
CI 19140|complex|Tartrazine: a yellow azo dye with sulfonate groups, sodium salt. Not drawn here.|C16H9N4Na3O9S2
CI 75470|complex|Carmine: a red pigment from cochineal insects, an aluminium salt of carminic acid. Not drawn here.|
Hydrolyzed Keratin|mixture|Keratin protein broken into peptide fragments of different sizes. A mixture.|
Hydrogenated Castor Oil|mixture|Castor oil that has been hydrogenated: mostly glyceryl tri(12-hydroxystearate), but a mixture.|
Dimethiconol|polymer|A short silicone polymer with -OH ends. A polymer, so there is no single structure.|
"""


def parse_structures():
    out = {}
    for line in STRUCTURES.strip().splitlines():
        parts = line.split("|")
        if len(parts) != 6:
            raise ValueError(f"Bad structure line ({len(parts)} fields): {line[:60]}")
        name, smiles, formula, cas, solubility, note = (p.strip() for p in parts)
        if name in out:
            raise ValueError("Duplicate structure entry: " + name)
        out[name] = {"smiles": smiles, "formula_expected": formula, "cas": cas or None,
                     "solubility": solubility or None, "note": note or None}
    return out


def parse_no_structure():
    out = {}
    for line in NO_STRUCTURE.strip().splitlines():
        parts = line.split("|")
        if len(parts) != 4:
            raise ValueError(f"Bad no-structure line ({len(parts)} fields): {line[:60]}")
        name, kind, note, formula = (p.strip() for p in parts)
        out[name] = {"kind": kind, "note": note, "formula_text": formula or None}
    return out

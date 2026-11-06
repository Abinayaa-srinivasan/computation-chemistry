import pytest
from app.chem import properties, parse_formula, cas_is_valid, parse_smiles, SmilesError
from app.main import create_app
from seed.chem_data import parse_structures, parse_no_structure
from seed.ingredients_data import parse
from seed.load import load

STRUCT = parse_structures()
OTHER = parse_no_structure()


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("db") / "t.db")
    load(path, quiet=True)
    return create_app(path).test_client()


def test_known_molecular_weights():
    # values from standard references (g/mol), tolerance for rounding of atomic weights
    known = {"Glycerin": 92.09, "Niacinamide": 122.12, "Caffeine": 194.19, "Retinol": 286.45,
             "Ascorbic Acid": 176.12, "Salicylic Acid": 138.12, "Cholesterol": 386.65, "Urea": 60.06}
    for name, mw in known.items():
        assert abs(properties(STRUCT[name]["smiles"])["mol_weight"] - mw) < 0.05, name


def test_every_formula_matches_its_structure():
    for name, d in STRUCT.items():
        assert properties(d["smiles"])["counts"] == parse_formula(d["formula_expected"]), name


def test_every_cas_check_digit_is_valid():
    for name, d in STRUCT.items():
        if d["cas"]:
            assert cas_is_valid(d["cas"]), (name, d["cas"])
    assert not cas_is_valid("56-81-6")


def test_every_ingredient_has_exactly_one_chemistry_entry():
    names = [i["inci_name"] for i in parse()]
    for n in names:
        assert (n in STRUCT) != (n in OTHER), n
    assert set(STRUCT) | set(OTHER) == set(names)


def test_property_counts():
    p = properties("OCC(O)CO")  # glycerol
    assert (p["hbd"], p["hba"], p["rotatable"], p["rings"]) == (3, 3, 2, 0)
    assert properties("CC1=CC=CC=C1")["rings"] == 1
    assert properties("[Na+].[Cl-]")["charge"] == 0
    assert properties("C[N+](C)(C)CC([O-])=O")["charge"] == 0


def test_bad_smiles_rejected():
    for bad in ("C(", "C1CC", "[Xx]", "Q"):
        with pytest.raises(SmilesError):
            parse_smiles(bad)


def test_api_shows_chemistry(client):
    items = client.get("/api/ingredients?q=niacinamide").json["ingredients"]
    d = client.get(f"/api/ingredients/{items[0]['id']}").json
    assert d["chem"]["formula"] == "C6H6N2O" and d["chem"]["kind"] == "molecule"
    assert d["chem"]["skin_penetration_hint"].startswith("Under 500")
    assert d["chem"]["pubchem_url"].startswith("https://pubchem.ncbi.nlm.nih.gov/")


def test_api_explains_mixtures(client):
    items = client.get("/api/ingredients?q=hyaluronate").json["ingredients"]
    d = client.get(f"/api/ingredients/{items[0]['id']}").json
    assert d["chem"]["kind"] == "polymer" and d["chem"]["smiles"] is None and d["chem"]["note"]


def test_ingredient_products_endpoint(client):
    items = client.get("/api/ingredients?q=glycerin").json["ingredients"]
    r = client.get(f"/api/ingredients/{items[0]['id']}/products").json["products"]
    assert r and all("name" in p and "position" in p for p in r)

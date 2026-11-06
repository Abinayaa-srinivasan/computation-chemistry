"""Tiny SMILES reader that CALCULATES molecular properties from a structure.

Why not RDKit? It cannot be installed in every environment, and this is easy to explain in a viva:
every number shown on the website is computed here from the structure string (SMILES), so the
formula, weight and counts always agree with the drawing. Only Kekule SMILES are supported
(alternating double bonds written out, no lower-case aromatic atoms).

Properties:
  formula      Hill order (C, H, then A-Z)
  mol_weight   sum of standard atomic weights, g/mol (Da)
  heavy_atoms  all atoms except hydrogen
  hbd / hba    Lipinski-style counts: hbd = hydrogens on N and O, hba = number of N and O atoms
  rotatable    single, non-ring bonds between two atoms that each have another heavy neighbour
  rings        cyclomatic number (independent rings)
  charge       sum of formal charges
"""
import re

ATOMIC_WEIGHT = {
    "H": 1.008, "B": 10.81, "C": 12.011, "N": 14.007, "O": 15.999, "F": 18.998, "Na": 22.990,
    "Mg": 24.305, "Al": 26.982, "Si": 28.085, "P": 30.974, "S": 32.06, "Cl": 35.45, "K": 39.098,
    "Ca": 40.078, "Ti": 47.867, "Fe": 55.845, "Cu": 63.546, "Zn": 65.38, "Br": 79.904, "I": 126.904,
}
# allowed valences for atoms written without brackets (first one that fits is used)
VALENCES = {"B": (3,), "C": (4,), "N": (3, 5), "O": (2,), "P": (3, 5), "S": (2, 4, 6), "Si": (4,),
            "F": (1,), "Cl": (1,), "Br": (1,), "I": (1,)}
ORGANIC = ("Cl", "Br", "B", "C", "N", "O", "P", "S", "F", "I")  # two-letter ones first
BOND_CHARS = {"-": 1, "=": 2, "#": 3}


class SmilesError(ValueError):
    pass


def parse_smiles(smiles):
    """Return (atoms, bonds). atoms: dicts {el, charge, h}. bonds: (a, b, order)."""
    atoms, bonds = [], []
    stack, ring_open = [], {}
    prev = None
    pending_order = None
    i, n = 0, len(smiles)
    while i < n:
        c = smiles[i]
        if c == "(":
            if prev is None:
                raise SmilesError("branch without atom")
            stack.append(prev); i += 1; continue
        if c == ")":
            if not stack:
                raise SmilesError("unbalanced )")
            prev = stack.pop(); i += 1; continue
        if c == ".":
            prev = None; pending_order = None; i += 1; continue
        if c in BOND_CHARS:
            pending_order = BOND_CHARS[c]; i += 1; continue
        if c in "/\\":  # stereo marks are ignored
            i += 1; continue
        if c.isdigit() or c == "%":
            if c == "%":
                num = smiles[i + 1:i + 3]; i += 3
            else:
                num = c; i += 1
            if prev is None:
                raise SmilesError("ring digit without atom")
            if num in ring_open:
                a, order = ring_open.pop(num)
                bonds.append((a, prev, pending_order or order or 1))
            else:
                ring_open[num] = (prev, pending_order)
            pending_order = None
            continue
        if c == "[":
            j = smiles.find("]", i)
            if j < 0:
                raise SmilesError("unclosed [")
            m = re.fullmatch(r"(\d*)([A-Z][a-z]?)(@{0,2})(?:(H)(\d*))?([+-]\d*|\+\+|--)?", smiles[i + 1:j])
            if not m:
                raise SmilesError("bad bracket atom: " + smiles[i:j + 1])
            el = m.group(2)
            if el not in ATOMIC_WEIGHT:
                raise SmilesError("unknown element " + el)
            h = int(m.group(5) or 1) if m.group(4) else 0
            ch = m.group(6) or ""
            if ch in ("++", "--"):
                charge = 2 if ch == "++" else -2
            elif ch:
                charge = (1 if ch[0] == "+" else -1) * int(ch[1:] or 1)
            else:
                charge = 0
            atoms.append({"el": el, "charge": charge, "h": h})
            i = j + 1
        else:
            el = next((o for o in ORGANIC if smiles.startswith(o, i)), None)
            if el is None and smiles.startswith("Si", i):
                el = "Si"
            if el is None:
                raise SmilesError(f"unexpected character {c!r} at {i}")
            atoms.append({"el": el, "charge": 0, "h": None})
            i += len(el)
        idx = len(atoms) - 1
        if prev is not None:
            bonds.append((prev, idx, pending_order or 1))
        pending_order = None
        prev = idx
    if stack:
        raise SmilesError("unbalanced (")
    if ring_open:
        raise SmilesError("unclosed ring")
    _fill_hydrogens(atoms, bonds)
    return atoms, bonds


def _fill_hydrogens(atoms, bonds):
    used = [0] * len(atoms)
    for a, b, o in bonds:
        used[a] += o; used[b] += o
    for k, at in enumerate(atoms):
        if at["h"] is None:
            options = VALENCES[at["el"]]
            val = next((v for v in options if v >= used[k]), options[-1])
            at["h"] = max(0, val - used[k])


def components(n, bonds):
    adj = [[] for _ in range(n)]
    for a, b, _ in bonds:
        adj[a].append(b); adj[b].append(a)
    seen, count = set(), 0
    for s in range(n):
        if s in seen:
            continue
        count += 1
        todo = [s]
        while todo:
            u = todo.pop()
            if u in seen:
                continue
            seen.add(u); todo.extend(adj[u])
    return count


def formula_counts(atoms):
    counts = {}
    for at in atoms:
        counts[at["el"]] = counts.get(at["el"], 0) + 1
        if at["h"]:
            counts["H"] = counts.get("H", 0) + at["h"]
    return counts


def hill(counts):
    def part(el):
        return el + (str(counts[el]) if counts[el] > 1 else "")
    order = []
    if "C" in counts:
        order.append("C")
        if "H" in counts:
            order.append("H")
        order += sorted(e for e in counts if e not in ("C", "H"))
    else:
        order = sorted(counts)
    return "".join(part(e) for e in order)


def parse_formula(text):
    """'C6H12O6' -> {'C': 6, 'H': 12, 'O': 6}; also accepts 'ZnO', 'Na3' and so on."""
    counts = {}
    for el, num in re.findall(r"([A-Z][a-z]?)(\d*)", text):
        counts[el] = counts.get(el, 0) + int(num or 1)
    return counts


def properties(smiles):
    atoms, bonds = parse_smiles(smiles)
    counts = formula_counts(atoms)
    weight = sum(ATOMIC_WEIGHT[e] * k for e, k in counts.items())
    ring_bonds = _ring_bonds(len(atoms), bonds)
    degree = [0] * len(atoms)
    for a, b, _ in bonds:
        degree[a] += 1; degree[b] += 1
    rotatable = sum(1 for k, (a, b, o) in enumerate(bonds)
                    if o == 1 and k not in ring_bonds and degree[a] > 1 and degree[b] > 1)
    return {
        "formula": hill(counts),
        "counts": counts,
        "mol_weight": round(weight, 2),
        "heavy_atoms": len(atoms),
        "hbd": sum(at["h"] for at in atoms if at["el"] in ("N", "O")),
        "hba": sum(1 for at in atoms if at["el"] in ("N", "O")),
        "rotatable": rotatable,
        "rings": len(bonds) - len(atoms) + components(len(atoms), bonds),
        "charge": sum(at["charge"] for at in atoms),
    }


def _ring_bonds(n, bonds):
    """Indexes of bonds that lie on a cycle (a bond is on a cycle if its ends stay connected without it)."""
    adj = [[] for _ in range(n)]
    for k, (a, b, _) in enumerate(bonds):
        adj[a].append((b, k)); adj[b].append((a, k))
    result = set()
    for k, (a, b, _) in enumerate(bonds):
        seen, todo = {a}, [a]
        found = False
        while todo and not found:
            u = todo.pop()
            for v, kk in adj[u]:
                if kk == k:
                    continue
                if v == b:
                    found = True; break
                if v not in seen:
                    seen.add(v); todo.append(v)
        if found:
            result.add(k)
    return result


def cas_is_valid(cas):
    """CAS registry numbers end with a check digit: sum(digit x position from the right) mod 10."""
    m = re.fullmatch(r"(\d{2,7})-(\d{2})-(\d)", cas or "")
    if not m:
        return False
    digits = (m.group(1) + m.group(2))[::-1]
    return sum((i + 1) * int(d) for i, d in enumerate(digits)) % 10 == int(m.group(3))

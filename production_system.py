# -------------------------------
# Rule-Based Production System
# Homework 2
# -------------------------------

from copy import deepcopy

# -------------------------------
# Unification Utilities
# -------------------------------

def is_variable(term):
    return isinstance(term, str) and term.startswith("?")

def unify(pattern, fact, bindings):
    """Attempt to unify a pattern with a fact given current bindings"""
    if bindings is None:
        return None

    if pattern == fact:
        return bindings

    if is_variable(pattern):
        return unify_var(pattern, fact, bindings)

    if isinstance(pattern, tuple) and isinstance(fact, tuple):
        if len(pattern) != len(fact):
            return None
        for p, f in zip(pattern, fact):
            bindings = unify(p, f, bindings)
            if bindings is None:
                return None
        return bindings

    return None

def unify_var(var, value, bindings):
    if var in bindings:
        return unify(bindings[var], value, bindings)
    bindings[var] = value
    return bindings

# -------------------------------
# Rule Class
# -------------------------------

class Rule:
    def __init__(self, name, antecedents, consequents, priority=0):
        self.name = name
        self.antecedents = antecedents
        self.consequents = consequents
        self.priority = priority

    def __repr__(self):
        return f"Rule({self.name})"

# -------------------------------
# Forward Chaining Engine
# -------------------------------

def match_antecedents(antecedents, wm, bindings=None):
    if bindings is None:
        bindings = {}

    if not antecedents:
        return [bindings]

    first, rest = antecedents[0], antecedents[1:]
    matches = []

    for fact in wm:
        new_bindings = unify(first, fact, deepcopy(bindings))
        if new_bindings is not None:
            matches.extend(match_antecedents(rest, wm, new_bindings))

    return matches

def instantiate(consequent, bindings):
    return tuple(bindings.get(term, term) for term in consequent)

# -------------------------------
# Conflict Resolution Strategies
# -------------------------------

def resolve_conflict(agenda, strategy="priority"):
    if strategy == "priority":
        return max(agenda, key=lambda x: x[0].priority)

    if strategy == "specificity":
        return max(agenda, key=lambda x: len(x[0].antecedents))

    if strategy == "order":
        return agenda[0]

    raise ValueError("Unknown conflict resolution strategy")

# -------------------------------
# Top-Level Production System
# -------------------------------

def run_ps(working_memory, rules, strategy="priority"):
    wm = list(working_memory)
    iteration = 0

    while True:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")
        agenda = []

        for rule in rules:
            bindings_list = match_antecedents(rule.antecedents, wm)
            for bindings in bindings_list:
                agenda.append((rule, bindings))

        if not agenda:
            print("No applicable rules. Halting.")
            break

        selected_rule, bindings = resolve_conflict(agenda, strategy)

        print(f"Firing rule: {selected_rule.name}")
        print(f"Bindings: {bindings}")

        new_facts = []
        for cons in selected_rule.consequents:
            fact = instantiate(cons, bindings)
            if fact not in wm:
                wm.append(fact)
                new_facts.append(fact)

        if not new_facts:
            print("No new facts inferred. Halting.")
            break

        for f in new_facts:
            print("  +", f)

    return wm
# -------------------------------
# Rule Base (from HW1)
# -------------------------------

rules = [

    Rule(
        "graduate-only-course-restriction",
        [
            ("graduate-only", "?course"),
            ("not-graduate-student", "?student")
        ],
        [("cannot-enroll-course", "?student", "?course")],
        priority=7
    ),
    Rule(
        "missing-prerequisite-prevents-enrollment",
        [
            ("course-prerequisite", "?course", "?prereq"),
            ("not-completed", "?student", "?prereq"),
            ("no-waiver", "?student", "?prereq")
        ],
        [("cannot-enroll-course", "?student", "?course")],
        priority=8
    ),


    Rule(
        "credit-limit-prevents-enrollment",
        [
            ("would-exceed-credit-limit", "?student", "?course")
        ],
        [("cannot-enroll-course", "?student", "?course")],
        priority=6
    ),

    Rule(
        "time-conflict-prevents-enrollment",
        [
            ("enrolled-in", "?student", "?sectionA"),
            ("request-section", "?student", "?sectionB"),
            ("section-overlap", "?sectionA", "?sectionB")
        ],
        [("cannot-enroll", "?student", "?sectionB")],
        priority=5
    )
]


if __name__ == "__main__":

    print("\n===== CONFLICT TEST CASE =====")

    WM_conflict = [
        ("student", "Bob"),
        ("request-course", "Bob", "CS550"),
        ("course-prerequisite", "CS550", "CS350"),
        ("not-completed", "Bob", "CS350"),
        ("no-waiver", "Bob", "CS350"),
        ("graduate-only", "CS550"),
        ("not-graduate-student", "Bob")
    ]

    print("\n=== PRIORITY strategy ===")
    run_ps(WM_conflict, rules, strategy="priority")

    print("\n=== SPECIFICITY strategy ===")
    run_ps(WM_conflict, rules, strategy="specificity")

    print("\n=== RULE ORDER strategy ===")
    run_ps(WM_conflict, rules, strategy="order")

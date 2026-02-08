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
    fired = set()
    cycle = 0

    while True:
        cycle += 1
        print(f"\nCYCLE {cycle}")
        print("\nCurrent WM:")
        for fact in wm:
            print(" ", fact)

        agenda = []
        any_new_fact = False

        for idx, rule in enumerate(rules, start=1):
            print(f"\nAttempting to match rule {idx}: {rule.name}")

            bindings_list = match_antecedents(rule.antecedents, wm)

            if not bindings_list:
                print("  Failing")
                continue

            print("  Match succeeds")

            for bindings in bindings_list:
                key = (rule.name, tuple(sorted(bindings.items())))
                if key not in fired:
                    agenda.append((rule, bindings))

        if not agenda:
            print("\nNO CHANGES ON LAST CYCLE, HALTING\n")
            break

        selected_rule, bindings = resolve_conflict(agenda, strategy)
        key = (selected_rule.name, tuple(sorted(bindings.items())))
        fired.add(key)

        print(f"\nFiring rule: {selected_rule.name}")
        print("Bindings:", bindings)

        for cons in selected_rule.consequents:
            fact = instantiate(cons, bindings)
            if fact not in wm:
                print("Adding assertions to WM:")
                print(" ", fact)
                wm.append(fact)
                any_new_fact = True

        if not any_new_fact:
            print("No new WM assertions")

    print("\nFinal WM:")
    for fact in wm:
        print(" ", fact)

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
    ),

    Rule(
    "administrative-hold-prevents-enrollment",
    [
        ("has-hold", "?student"),
        ("request-course", "?student", "?course")
    ],
    [("cannot-enroll-course", "?student", "?course")],
    priority=9
    ),


    Rule(
    "cannot-enroll-course-implies-drop-request",
    [
        ("cannot-enroll-course", "?student", "?course"),
        ("request-course", "?student", "?course")
    ],
    [("dropped-request", "?student", "?course")],
    priority=4
    ),
    Rule(
    "dropped-request-implies-notify-student",
    [
        ("dropped-request", "?student", "?course")
    ],
    [("notified-student", "?student", "?course")],
    priority=3
    )

]




if __name__ == "__main__":

    # -------------------------------
    # Define Working Memories
    # -------------------------------

    working_memories = {
        "CONFLICT TEST CASE": [
            ("student", "Carol"),
            ("request-course", "Carol", "CS550"),
            ("graduate-only", "CS550"),
            ("not-graduate-student", "Carol"),
            ("course-prerequisite", "CS550", "CS350"),
            ("not-completed", "Carol", "CS350"),
            ("no-waiver", "Carol", "CS350"),
            ("has-hold", "Carol")
        ],

        "NO-MATCH TEST CASE": [
            ("student", "Eve"),
            ("likes", "Eve", "AI"),
            ("hobby", "Eve", "Chess")
        ]
    }

    strategies = ["priority", "specificity", "order"]

    for wm_name, wm in working_memories.items():

        print("\n" + "=" * 60)
        print(f"TEST CASE: {wm_name}")
        print("=" * 60)

        for strategy in strategies:

            # No need to run all strategies for no-match case
            if wm_name == "NO-MATCH TEST CASE" and strategy != "priority":
                continue

            print(f"\n=== {strategy.upper()} strategy ===")
            run_ps(wm, rules, strategy=strategy)

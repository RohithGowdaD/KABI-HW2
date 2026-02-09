from copy import deepcopy

# Helper Functions

def is_var(term):
    # Variables start with '?'
    return isinstance(term, str) and term.startswith("?")

def unify(pattern, fact, bindings):
    # Base case: if bindings failed previously
    if bindings is None:
        return None

    # precise match
    if pattern == fact:
        return bindings

    # Variable handling
    if is_var(pattern):
        return unify_var(pattern, fact, bindings)
    if is_var(fact):
        return unify_var(fact, pattern, bindings)

    # Recursive check for tuples (antecedents/facts)
    if isinstance(pattern, tuple) and isinstance(fact, tuple):
        if len(pattern) != len(fact):
            return None
        
        # Check every element in the tuple
        current_bindings = dict(bindings)
        for p, f in zip(pattern, fact):
            current_bindings = unify(p, f, current_bindings)
            if current_bindings is None:
                return None
        return current_bindings

    return None

def unify_var(var, val, bindings):
    if var == val:
        return bindings
    
    # if var is already bound, check consistency
    if var in bindings:
        return unify(bindings[var], val, bindings)
    
    # if val is a variable and bound, check consistency
    if is_var(val) and val in bindings:
        return unify(var, bindings[val], bindings)

    # Bind it
    new_b = dict(bindings)
    new_b[var] = val
    return new_b

def instantiate(pattern, bindings):
    # Fills in the variables in the consequent
    result = []
    for term in pattern:
        if is_var(term):
            result.append(bindings.get(term, term))
        else:
            result.append(term)
    return tuple(result)

# Core Classes

class Rule:
    def __init__(self, name, lhs, rhs, priority=0):
        self.name = name
        self.lhs = lhs  # antecedents (conditions)
        self.rhs = rhs  # consequents (actions)
        self.priority = priority

    def __repr__(self):
        return f"<Rule: {self.name}>"

# Forward Chaining Logic

def match_rules(lhs, wm, bindings=None, supports=None):
    # DFS to find all valid variable bindings for a rule
    if bindings is None: bindings = {}
    if supports is None: supports = []

    if not lhs:
        return [(bindings, supports)]

    first_condition = lhs[0]
    remaining = lhs[1:]
    
    found_matches = []

    for fact in wm:
        # Try to unify the first condition with every fact in memory
        new_bindings = unify(first_condition, fact, bindings)
        
        if new_bindings is not None:
            # If it works, recurse for the rest of the conditions
            found_matches.extend(
                match_rules(remaining, wm, new_bindings, supports + [fact])
            )

    return found_matches

def get_activation_key(rule, bindings):
    # We need a unique key to prevent firing the same instantiation twice (Refraction).
    # Sorting items ensures dict order doesn't mess up the key.
    return (id(rule), tuple(sorted(bindings.items())))

def select_rule(agenda, strategy):
    if not agenda:
        return None

    # agenda item structure: (rule, bindings, supports, index, key)
    
    if strategy == "priority":
        # 1. Priority (High to low)
        # 2. Specificity (More conditions = better)
        # 3. Recency/Order (Lower index first, hence negative for max)
        return max(agenda, key=lambda x: (x[0].priority, len(x[0].lhs), -x[3]))

    elif strategy == "specificity":
        # 1. Specificity (Length of LHS)
        # 2. Priority
        # 3. Order
        return max(agenda, key=lambda x: (len(x[0].lhs), x[0].priority, -x[3]))

    elif strategy == "order":
        # Just take the first one found in the rule list
        return min(agenda, key=lambda x: x[3])
    
    else:
        print(f"Error: Unknown strategy {strategy}")
        return None

# --- Explanation System ---

def print_explanation(fact, history, indent=0, printed=None):
    if printed is None: printed = set()
    
    spacer = "  " * indent
    
    # avoid infinite recursion loops in output
    if fact in printed:
        print(f"{spacer}- {fact} (see above)")
        return
    printed.add(fact)

    data = history.get(fact)
    if not data:
        print(f"{spacer}- {fact} [Unknown source]")
        return

    if data['type'] == 'given':
        print(f"{spacer}- {fact} [asserted]")
    else:
        print(f"{spacer}- {fact} [inferred by {data['rule']}]")
        print(f"{spacer}  Bindings: {data['bindings']}")
        print(f"{spacer}  Supports:")
        for s in data['supports']:
            print_explanation(s, history, indent + 2, printed)

# Main Engine

def run_ps(start_wm, rules, strategy="priority", verbose=True):
    wm = list(start_wm)
    fired_history = set() # For refraction
    
    # Track provenance for explanations
    # structure: fact -> {type: 'given'/'inferred', rule: ..., bindings: ..., supports: ...}
    provenance = {f: {'type': 'given'} for f in wm}

    step = 0
    max_steps = 100 # Safety break

    while step < max_steps:
        if verbose:
            print(f"\n--- CYCLE {step + 1} ---")
            print("Current WM:")
            for item in wm:
                print(f"  {item}")
            print("-" * 20)

        agenda = []

        # 1. MATCH
        for i, r in enumerate(rules):
            if verbose: print(f"Attempting to match rule: {r.name}")
            
            matches = match_rules(r.lhs, wm)
            
            # Filter matches that have already fired (Refraction)
            new_activations = []
            for b, s in matches:
                key = get_activation_key(r, b)
                if key not in fired_history:
                    new_activations.append((r, b, s, i, key))

            # Logging for the assignment requirements
            if verbose:
                if not matches:
                    print("  Failing (no match)")
                elif not new_activations:
                    print("  Failing (all matches already fired)")
                else:
                    print(f"  Match succeeds ({len(new_activations)} new activations)")
            
            agenda.extend(new_activations)

        if not agenda:
            if verbose: print("\nNO CHANGES ON LAST CYCLE, HALTING")
            break

        # 2. RESOLVE
        selected = select_rule(agenda, strategy)
        rule, bindings, supports, idx, key = selected
        
        fired_history.add(key)
        step += 1

        if verbose:
            print(f"\n>>> FIRING rule: {rule.name}")
            print(f"    Bindings: {bindings}")

        # 3. ACT
        new_facts_added = False
        if verbose: print("    Adding assertions to WM:")
        
        for rhs_pattern in rule.rhs:
            new_fact = instantiate(rhs_pattern, bindings)
            
            if new_fact not in wm:
                wm.append(new_fact)
                provenance[new_fact] = {
                    'type': 'inferred',
                    'rule': rule.name,
                    'bindings': bindings,
                    'supports': deepcopy(supports)
                }
                new_facts_added = True
                if verbose: print(f"      + {new_fact}")
        
        if not new_facts_added and verbose:
            print("    No new WM assertions from this activation.")

    return wm, provenance

# --- Runner ---

def run_tests():
    # --- RULE SET 1: Enrollment ---
    # Standard HW1 rules
    enrollment_rules = [
        Rule("graduate-only-course-restriction",
             [("graduate-only", "?course"), ("not-graduate-student", "?student")],
             [("cannot-enroll-course", "?student", "?course")],
             priority=7),
        
        Rule("missing-prerequisite-prevents-enrollment",
             [("course-prerequisite", "?course", "?prereq"), ("not-completed", "?student", "?prereq"), ("no-waiver", "?student", "?prereq")],
             [("cannot-enroll-course", "?student", "?course")],
             priority=8),
             
        Rule("credit-limit-prevents-enrollment",
             [("would-exceed-credit-limit", "?student", "?course")],
             [("cannot-enroll-course", "?student", "?course")],
             priority=6),
             
        Rule("time-conflict-prevents-enrollment",
             [("enrolled-in", "?student", "?secA"), ("request-section", "?student", "?secB"), ("section-overlap", "?secA", "?secB")],
             [("cannot-enroll-section", "?student", "?secB")],
             priority=5)
    ]

    wm_enrollment = [
        ("graduate-only", "CS500"),
        ("not-graduate-student", "Alice"),
        ("course-prerequisite", "CS500", "CS400"),
        ("not-completed", "Alice", "CS400"),
        ("no-waiver", "Alice", "CS400"),
        ("would-exceed-credit-limit", "Alice", "CS500"),
        ("enrolled-in", "Alice", "SEC001"),
        ("request-section", "Alice", "SEC010"),
        ("section-overlap", "SEC001", "SEC010"),
    ]

    print("\n" + "="*30 + " CASE 1: ENROLLMENT CONFLICTS " + "="*30)
    
    # Just running priority for the main demonstration
    final_wm, why = run_ps(wm_enrollment, enrollment_rules, strategy="priority")
    
    print("\n--- Explanations (Priority Strategy) ---")
    targets = [("cannot-enroll-course", "Alice", "CS500"), ("cannot-enroll-section", "Alice", "SEC010")]
    for t in targets:
        print(f"\nWhy {t}?")
        print_explanation(t, why)


    # --- RULE SET 2: Provenance Strategy Test ---
    # This set tests if strategies pick different 'causes' for the same problem
    provenance_rules = [
        Rule("risk-from-credit-overload", 
             [("credit-overload", "?s")], 
             [("needs-advisor-review", "?s")], priority=6),
             
        Rule("risk-from-probation", 
             [("academic-probation", "?s")], 
             [("needs-advisor-review", "?s")], priority=9), # Highest priority
             
        Rule("specific-risk-combo", 
             [("credit-overload", "?s"), ("has-time-conflict", "?s")], 
             [("needs-advisor-review", "?s")], priority=7), # Most specific
             
        Rule("risk-from-time-conflict", 
             [("has-time-conflict", "?s")], 
             [("needs-advisor-review", "?s")], priority=6),
             
        Rule("create-hold-after-review", 
             [("needs-advisor-review", "?s")], 
             [("registration-hold", "?s")], priority=5)
    ]

    wm_prov = [
        ("credit-overload", "Bob"),
        ("academic-probation", "Bob"),
        ("has-time-conflict", "Bob")
    ]

    print("\n\n" + "="*30 + " CASE 2: STRATEGY COMPARISON " + "="*30)
    
    strategies = ["priority", "specificity", "order"]
    
    for s in strategies:
        print(f"\n" + "*"*20 + f" STRATEGY: {s.upper()} " + "*"*20)
        final_wm, why = run_ps(wm_prov, provenance_rules, strategy=s)
        
        # We want to see how the hold was derived
        target = ("registration-hold", "Bob")
        if target in final_wm:
            print(f"\nExplanation path for {target}:")
            print_explanation(target, why)

if __name__ == "__main__":
    run_tests()
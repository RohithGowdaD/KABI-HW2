# Homework 2: Rule-Based System Implementation

**Course:** CSCI-B 552 Knowledge Based AI (Spring 2026)
**Authors:** Logan Reddell, Niloy Deb Roy Mishu, and Rohith Gowda Devaraju
**Language:** Python 3.13

## Overview
This project implements a domain-independent, forward-chaining production system. It features a recursive unification engine, multiple conflict resolution strategies, and a provenance-based explanation component. The system is demonstrated using two distinct rule sets: University Enrollment (logic from HW1) and a Risk Assessment scenario (for testing conflict resolution strategies).

## File Structure
* `production_system.py`: The main source code containing the inference engine, rule definitions, and test runner.
* `README.md`: System documentation and usage instructions.

## Prerequisites
* Python 3.x (Tested on Python 3.13)
* Standard libraries only (requires `copy`). No external `pip` installation is necessary.

## How to Run
Open your terminal or command prompt, navigate to the project directory, and run:

    python production_system.py > output.txt

### Expected Output
The program will automatically run two test cases:
1.  **Case 1 (Enrollment):** Demonstrates the `Priority` strategy solving a course enrollment conflict.
2.  **Case 2 (Strategy Comparison):** Runs the same data against `Priority`, `Specificity`, and `Order` strategies to demonstrate how the inference path changes based on the chosen strategy.

At the end of each run, the system prints the **Explanation Trace**, detailing exactly how specific facts were derived.

## System Features

### 1. Inference Engine
* **Forward Chaining:** Iteratively matches rules against Working Memory (WM) until no new facts can be derived.
* **Unification:** Supports variable binding (e.g., `?student` binding to `Alice`) across multiple antecedents.
* **Refraction:** Implements a history mechanism to prevent the same rule instantiation (Rule + Bindings) from firing multiple times, avoiding infinite loops.

### 2. Conflict Resolution Strategies
The system implements three strategies to select which rule to fire when multiple rules match:
* **Priority:** Selects the rule with the highest manually assigned `priority` value.
* **Specificity:** Selects the rule with the highest number of antecedents (conditions).
* **Order:** Selects the first matching rule found in the rule list (default/recency).

### 3. Explanation Component
The system tracks the "provenance" of every fact. It records:
* The rule that generated the fact.
* The variable bindings used at the moment of inference.
* The supporting facts that triggered the rule.
This allows the system to recursively print a derivation tree (e.g., "Fact A was inferred by Rule X, which was supported by Fact B...").

## Rule Sets

### Rule Set 1: Enrollment Logic
Models constraints for university registration, including:
* `graduate-only-course-restriction`
* `missing-prerequisite-prevents-enrollment`
* `credit-limit-prevents-enrollment`
* `time-conflict-prevents-enrollment`

### Rule Set 2: Provenance & Strategy Test
Designed to test conflict resolution by providing multiple valid reasons for a single outcome (`needs-advisor-review`).

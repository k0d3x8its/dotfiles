# Interface Design for Testability

Design decisions made before writing tests determine how hard (or easy) the tests
will be to write and maintain.

> Examples use Python. Patterns apply to any language.

## 1. Accept dependencies, don't create them

```python
# TESTABLE: dependency injected
def process_order(order, payment_gateway):
    return payment_gateway.charge(order.total)

# HARD TO TEST: dependency created internally
def process_order(order):
    gateway = StripeGateway(os.environ["KEY"])
    return gateway.charge(order.total)
```

The injectable version can be tested with any object that has a `.charge()` method —
real, fake, or mock.

## 2. Return results, don't produce side effects

```python
# TESTABLE: returns a value
def calculate_discount(cart) -> Discount:
    ...
    return Discount(amount=amount, reason=reason)

# HARD TO TEST: mutates in place
def apply_discount(cart) -> None:
    cart.total -= calculate_amount(cart)
```

Functions that return values can be asserted on directly. Functions that mutate state
require inspecting side effects — more setup, more fragility.

## 3. Small surface area

- Fewer public functions = fewer tests needed
- Fewer parameters = simpler test setup
- One conceptual operation per function = one test per behavior

Ask before writing: "Can I express this as one function that takes a value and returns
a value?" If yes, start there.

## 4. Separate I/O from logic

```python
# HARD TO TEST: logic mixed with I/O
def run_report(filepath):
    data = json.load(open(filepath))
    total = sum(item["price"] for item in data["items"])
    print(f"Total: {total}")

# TESTABLE: I/O at the edges, logic in the middle
def calculate_total(items: list[dict]) -> float:
    return sum(item["price"] for item in items)

def run_report(filepath):            # thin I/O shell
    data = json.load(open(filepath))
    total = calculate_total(data["items"])
    print(f"Total: {total}")
```

Test `calculate_total` directly with fixture data — no file system needed.
The I/O shell (`run_report`) needs at most one integration test.

## 5. Seams

A seam is a place where behavior can be altered without editing at that place.
Good interface design creates seams naturally.

*(Full seam reference: `~/.claude/references/code/CODE-REFERENCE.md`)*

If a function is hard to test, it usually lacks a seam. Introduce one:
- Extract the dependency and accept it as a parameter
- Wrap the external call behind a simple interface
- Use a config/env variable to change behavior at load time

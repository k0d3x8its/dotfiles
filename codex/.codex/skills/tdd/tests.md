# Good and Bad Tests

> Examples use Python/pytest. Patterns apply to any test runner.

## Good Tests

Integration-style: test through real interfaces, not mocks of internal parts.

```python
# GOOD: tests observable behavior through public interface
def test_user_can_checkout_with_valid_cart():
    cart = Cart()
    cart.add(product)
    result = checkout(cart, payment_method)
    assert result.status == "confirmed"
```

Characteristics:
- Tests behavior callers care about
- Uses public API only
- Survives internal refactors
- Describes WHAT, not HOW
- One logical assertion per test (can have multiple `assert` lines if they verify one thing)

## Bad Tests

Coupled to implementation details.

```python
# BAD: tests implementation details
def test_checkout_calls_payment_service():
    with patch('myapp.payment_service.process') as mock_process:
        checkout(cart, payment)
    mock_process.assert_called_once_with(cart.total)
```

Red flags:
- Mocking internal collaborators
- Testing private methods / functions with leading `_`
- Asserting on call counts or call order
- Test breaks when refactoring without behavior change
- Test name describes HOW not WHAT
- Verifying state by querying internals instead of using the interface

```python
# BAD: bypasses interface to verify
def test_create_user_saves_to_database():
    create_user(name="Alice")
    row = db.execute("SELECT * FROM users WHERE name = ?", ("Alice",)).fetchone()
    assert row is not None

# GOOD: verifies through interface
def test_create_user_makes_user_retrievable():
    user = create_user(name="Alice")
    retrieved = get_user(user.id)
    assert retrieved.name == "Alice"
```

## One Logical Assertion Per Test

Tests with multiple unrelated assertions hide which behavior failed.

```python
# BAD: two behaviors in one test
def test_cart():
    cart = Cart()
    cart.add(item)
    assert len(cart.items) == 1        # behavior 1
    assert cart.total == item.price    # behavior 2

# GOOD: one behavior per test
def test_cart_tracks_added_items():
    cart = Cart()
    cart.add(item)
    assert len(cart.items) == 1

def test_cart_total_reflects_added_items():
    cart = Cart()
    cart.add(item)
    assert cart.total == item.price
```

## Test Naming

Name describes the behavior being verified, not the method being called.

```python
# BAD: names the method
def test_checkout():
def test_process_payment():

# GOOD: names the behavior
def test_checkout_confirms_order_with_valid_payment():
def test_checkout_rejects_empty_cart():
def test_checkout_returns_error_on_payment_failure():
```

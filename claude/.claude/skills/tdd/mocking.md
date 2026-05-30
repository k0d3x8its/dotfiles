# Mocking Guidelines

> Examples use Python/unittest.mock. Apply the same rules with your stack's mock library.

## When to mock

Mock at **system boundaries** only:

- External APIs (payment processors, email services, external HTTP)
- Time and randomness (`datetime.now()`, `random`, `uuid`)
- File system (when testing logic, not I/O)
- External processes or subshells

Do not mock:
- Your own modules or classes
- Internal collaborators
- Anything you control and can instantiate directly

## Designing for mockability

At system boundaries, design interfaces that are easy to mock.

### Use dependency injection

Pass external dependencies in rather than constructing them internally:

```python
# EASY TO MOCK: dependency injected
def process_payment(order, payment_client):
    return payment_client.charge(order.total)

# HARD TO MOCK: dependency created internally
def process_payment(order):
    client = StripeClient(os.environ["STRIPE_KEY"])
    return client.charge(order.total)
```

Test the injectable version:

```python
def test_process_payment_charges_correct_amount():
    mock_client = Mock()
    mock_client.charge.return_value = PaymentResult(success=True)

    result = process_payment(order, mock_client)

    mock_client.charge.assert_called_once_with(order.total)
    assert result.success
```

### Prefer SDK-style interfaces over generic fetchers

Specific functions per operation are easier to mock than one generic function:

```python
# GOOD: each function independently mockable
class ApiClient:
    def get_user(self, user_id): ...
    def get_orders(self, user_id): ...
    def create_order(self, data): ...

# BAD: mocking requires conditional logic inside the mock
class ApiClient:
    def fetch(self, endpoint, method="GET", body=None): ...
```

The SDK approach means:
- Each mock returns one specific shape
- No conditional logic in test setup
- Clear which endpoint a test exercises

## Mocking time

```python
from unittest.mock import patch
from datetime import datetime

def test_order_timestamp_is_set_on_creation():
    fixed_time = datetime(2026, 1, 1, 12, 0, 0)
    with patch("myapp.orders.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_time
        order = create_order(cart)
    assert order.created_at == fixed_time
```

## Real vs mock database

Prefer a real test database (SQLite in-memory, test-scoped Postgres) over mocking
the database layer. Mocking the DB hides query errors and schema mismatches that only
surface against a real engine.

```python
# pytest fixture — real SQLite in memory
@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield Session(engine)
    engine.dispose()
```

Only mock the database when: the test is purely about business logic and the DB
interaction is irrelevant to what's being verified.

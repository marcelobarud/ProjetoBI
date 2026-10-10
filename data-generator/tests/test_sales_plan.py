from collections import Counter
from types import SimpleNamespace

from projectbi_generator.sales_plan import CustomerFrequencyTickets


SHARES = {
    "individual": {"one": 42, "two_to_four": 38, "five_to_ten": 16, "eleven_plus": 4},
    "business": {"one": 25, "two_to_four": 45, "five_to_ten": 25, "eleven_plus": 5},
}


def test_customer_frequency_tickets_are_reproducible_and_conserve_target():
    customers = [
        *(SimpleNamespace(code=f"PF-{index:05d}", customer_type="individual") for index in range(9_000)),
        *(SimpleNamespace(code=f"PJ-{index:05d}", customer_type="business") for index in range(1_000)),
    ]
    first = CustomerFrequencyTickets(customers, 10_000, SHARES, 12345)
    second = CustomerFrequencyTickets(customers, 10_000, SHARES, 12345)

    assert first.tickets == second.tickets
    assert len(first.tickets) == 10_000
    frequency = Counter(first.tickets)
    by_type = {
        kind: Counter(frequency[customer.code] for customer in customers
                      if customer.customer_type == kind and frequency[customer.code])
        for kind in ("individual", "business")
    }
    averages = {
        kind: sum(count * orders for orders, count in counts.items()) / sum(counts.values())
        for kind, counts in by_type.items()
    }
    assert averages["business"] > averages["individual"]
    total = sum(sum(counts.values()) for counts in by_type.values())
    bucket_shares = {
        "one": sum(counts[1] for counts in by_type.values()) * 100 / total,
        "two_to_four": sum(sum(counts[value] for value in range(2, 5)) for counts in by_type.values()) * 100 / total,
        "five_to_ten": sum(sum(counts[value] for value in range(5, 11)) for counts in by_type.values()) * 100 / total,
        "eleven_plus": sum(sum(count for value, count in counts.items() if value >= 11)
                            for counts in by_type.values()) * 100 / total,
    }
    assert abs(sum(bucket_shares.values()) - 100) < 1e-9
    assert 35 <= bucket_shares["one"] <= 50
    assert 30 <= bucket_shares["two_to_four"] <= 40
    assert 10 <= bucket_shares["five_to_ten"] <= 18
    assert 2 <= bucket_shares["eleven_plus"] <= 6

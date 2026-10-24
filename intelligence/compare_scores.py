import math
from intelligence.features import get_domain_features


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def compare_scores():
    domains = get_domain_features()

    if not domains:
        return []

    time_values = [
        math.log1p(d["total_time_seconds"]) for d in domains
    ]
    activation_values = [
        math.log1p(d["activation_count"]) for d in domains
    ]

    max_time = max(time_values)
    max_activations = max(activation_values)

    results = []

    for d, t, a in zip(domains, time_values, activation_values):
        recency = d["recency_seconds"]

        time_score = t / max_time if max_time else 0.0
        activation_score = (
            a / max_activations if max_activations else 0.0
        )
        recency_score = (
            math.exp(-recency / 1800)
            if recency is not None else 0.0
        )

        vector = [time_score, activation_score, recency_score]

        # Approach A: weighted baseline.
        weighted_score = (
            0.40 * time_score
            + 0.35 * activation_score
            + 0.25 * recency_score
        )

        # Approach B: similarity to an ideal high-engagement profile.
        similarity = cosine_similarity(vector, [1.0, 1.0, 1.0])
        feature_strength = sum(vector) / 3
        similarity_score = similarity * feature_strength

        # Approach C: 50/50 hybrid.
        hybrid_score = (weighted_score + similarity_score) / 2

        results.append({
            "domain": d["domain"],
            "time_score": round(time_score, 3),
            "activation_score": round(activation_score, 3),
            "recency_score": round(recency_score, 3),
            "weighted_score": round(weighted_score, 3),
            "similarity_score": round(similarity_score, 3),
            "hybrid_score": round(hybrid_score, 3),
        })

    return sorted(
        results,
        key=lambda item: item["hybrid_score"],
        reverse=True,
    )


if __name__ == "__main__":
    for result in compare_scores():
        print(result)

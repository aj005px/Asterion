import math

from intelligence.features import get_domain_features


def cosine_similarity(a, b):
    dot_product = sum(x * y for x, y in zip(a, b))

    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def build_similarity_graph():
    domains = get_domain_features()

    if not domains:
        print("No domain data available.")
        return [], []

    # Log scaling reduces the effect of unusually large values.
    times = [
        math.log1p(d["total_time_seconds"])
        for d in domains
    ]
    activations = [
        math.log1p(d["activation_count"])
        for d in domains
    ]

    max_time = max(times)
    max_activations = max(activations)

    vectors = []

    for d, time_value, activation_value in zip(
        domains, times, activations
    ):
        time_score = (
            time_value / max_time if max_time else 0.0
        )

        activation_score = (
            activation_value / max_activations
            if max_activations else 0.0
        )

        recency = d["recency_seconds"]
        recency_score = (
            math.exp(-recency / 1800)
            if recency is not None else 0.0
        )

        vectors.append({
            "domain": d["domain"],
            "vector": [
                time_score,
                activation_score,
                recency_score,
            ],
        })

    # Compare every domain with every other domain.
    matrix = []

    for first in vectors:
        row = []

        for second in vectors:
            similarity = cosine_similarity(
                first["vector"],
                second["vector"],
            )
            row.append(similarity)

        matrix.append(row)

    # Each undirected edge appears only once.
    edges = []

    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            edges.append({
                "source": vectors[i]["domain"],
                "target": vectors[j]["domain"],
                "similarity": matrix[i][j],
            })

    edges.sort(
        key=lambda edge: edge["similarity"],
        reverse=True,
    )

    return [
        {
            "domain": item["domain"],
            "vector": item["vector"],
        }
        for item in vectors
    ], edges


if __name__ == "__main__":
    nodes, edges = build_similarity_graph()

    print("\n=== DOMAIN FEATURE VECTORS ===")
    for node in nodes:
        print(
            f'{node["domain"]}: '
            f'{[round(x, 3) for x in node["vector"]]}'
        )

    print("\n=== TOP 10 MOST SIMILAR DOMAIN PAIRS ===")
    for edge in edges[:10]:
        print(
            f'{edge["source"]} <-> {edge["target"]}: '
            f'{edge["similarity"]:.3f}'
        )

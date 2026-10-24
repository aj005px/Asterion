import math
import webbrowser
from pathlib import Path
from html import escape

from intelligence.similarity_graph import build_similarity_graph


def build_html():
    nodes, edges = build_similarity_graph()

    if not nodes:
        print("No domain data available.")
        return

    width, height = 1000, 750
    cx, cy = width / 2, height / 2
    radius = 260
    count = len(nodes)

    positions = {}

    for i, node in enumerate(nodes):
        angle = 2 * math.pi * i / count - math.pi / 2
        positions[node["domain"]] = (
            cx + radius * math.cos(angle),
            cy + radius * math.sin(angle),
        )

    svg = []

    # Draw every possible edge; JavaScript filters them by threshold.
    for edge in edges:
        x1, y1 = positions[edge["source"]]
        x2, y2 = positions[edge["target"]]
        similarity = edge["similarity"]

        svg.append(
            f'<g class="edge" data-sim="{similarity:.6f}">'
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" '
            f'x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#58a6ff" stroke-opacity="0.8" '
            f'stroke-width="{1 + similarity * 2:.1f}"/>'
            f'<text x="{(x1+x2)/2:.1f}" '
            f'y="{(y1+y2)/2-8:.1f}" text-anchor="middle" '
            f'fill="#8b949e" font-size="12">'
            f'{similarity:.3f}</text></g>'
        )

    for node in nodes:
        domain = node["domain"]
        x, y = positions[domain]
        vector = node["vector"]
        strength = sum(vector) / 3
        node_radius = 12 + 12 * strength

        svg.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" '
            f'r="{node_radius:.1f}" fill="#238636" '
            f'stroke="#3fb950" stroke-width="2"/>'
        )

        svg.append(
            f'<text x="{x:.1f}" y="{y + node_radius + 22:.1f}" '
            f'text-anchor="middle" fill="#e6edf3" '
            f'font-size="14">{escape(domain)}</text>'
        )

        vector_text = ", ".join(f"{v:.2f}" for v in vector)
        svg.append(
            f'<text x="{x:.1f}" y="{y + node_radius + 40:.1f}" '
            f'text-anchor="middle" fill="#8b949e" '
            f'font-size="11">[{vector_text}]</text>'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Asterion Similarity Graph</title>
<style>
body {{
    background: #0d1117; color: #e6edf3;
    font-family: Arial, sans-serif; margin: 0; padding: 24px;
}}
h1 {{ color: #58a6ff; }}
p {{ color: #8b949e; }}
.controls {{ margin: 20px 0; }}
input {{ width: 280px; }}
svg {{ width: 100%; max-width: 1000px; height: auto; }}
.edge {{ transition: opacity 0.15s; }}
</style>
</head>
<body>
<h1>Asterion — Domain Similarity Graph</h1>
<p>Adjust the minimum cosine similarity to explore the network.</p>

<div class="controls">
  <label for="threshold">Similarity threshold: </label>
  <strong id="value">0.90</strong>
  <br><br>
  <input id="threshold" type="range"
         min="0.50" max="1.00" step="0.01" value="0.90">
  <p id="stats"></p>
</div>

<svg viewBox="0 0 {width} {height}"
     xmlns="http://www.w3.org/2000/svg">
{''.join(svg)}
</svg>

<script>
const slider = document.getElementById("threshold");
const value = document.getElementById("value");
const stats = document.getElementById("stats");
const edges = [...document.querySelectorAll(".edge")];

function updateGraph() {{
    const threshold = Number(slider.value);
    let visible = 0;

    edges.forEach(edge => {{
        const similarity = Number(edge.dataset.sim);
        const show = similarity >= threshold;
        edge.style.display = show ? "" : "none";
        if (show) visible++;
    }});

    value.textContent = threshold.toFixed(2);
    stats.textContent =
        `${{visible}} connections shown out of ${{edges.length}} possible pairs.`;
}}

slider.addEventListener("input", updateGraph);
updateGraph();
</script>
</body>
</html>
"""

    output = Path("asterion_similarity_graph.html").resolve()
    output.write_text(html, encoding="utf-8")

    print(f"Graph saved to: {output}")
    webbrowser.open(output.as_uri())


if __name__ == "__main__":
    build_html()

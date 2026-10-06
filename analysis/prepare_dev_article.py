"""Prepare paste-ready DEV text with verified, immutable public image URLs."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_COMMIT = "c65372066e6cf9357e0867a2b69b0667dc8f1e87"
PUBLIC_ROOT = f"https://raw.githubusercontent.com/gracelee087/ai-marketing-honesty-bench/{ASSET_COMMIT}/"


def main():
    draft = (ROOT / "post/draft.md").read_text(encoding="utf-8")
    title = re.search(r'^title: "(.*)"$', draft, re.M).group(1)
    tags = re.search(r"^tags: (.*)$", draft, re.M).group(1)
    body = re.sub(r"\A---\n.*?\n---\n", "", draft, count=1, flags=re.S).lstrip()
    images = []

    def public_image(match):
        path = (ROOT / "post" / match.group(2)).resolve()
        assert path.is_file() and path.suffix == ".png"
        relative = path.relative_to(ROOT).as_posix()
        url = PUBLIC_ROOT + relative
        images.append(url)
        return f"![{match.group(1)}]({url})"

    body = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", public_image, body)
    assert len(images) == 3
    assert body.count("{% details ") == body.count("{% enddetails %}") == 9
    for heading in ("What I Benchmarked", "Models Tested", "Findings", "My Benchmark"):
        assert f"## {heading}" in body
    assert "](../" not in body
    (ROOT / "post/dev_body.txt").write_text(body, encoding="utf-8")
    fields = f"TITLE\n{title}\n\nTAGS\n{tags}\n\nBODY\nCopy the entire contents of dev_body.txt into the DEV article body.\n\nIMAGES\nAll three figures use verified public image URLs. They are already embedded in the body.\n\nPUBLIC BENCHMARK\nhttps://www.kaggle.com/benchmarks/sohee087/which-ai-lies-less-in-marketing-copy\n\nRESEARCH REPOSITORY\nhttps://github.com/gracelee087/ai-marketing-honesty-bench\n"
    (ROOT / "post/dev_fields.txt").write_text(fields, encoding="utf-8")
    print("Prepared DEV body and fields: 4 template sections, 9 expandable details, 3 public figures.")


if __name__ == "__main__":
    main()

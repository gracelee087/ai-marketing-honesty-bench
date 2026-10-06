"""Make a self-contained HTML preview of the existing DEV Markdown draft."""
import base64
import html
import re

import markdown

from analyze import ROOT


def main():
    path = ROOT / "post" / "draft.md"
    source = path.read_text(encoding="utf-8")
    title = re.search(r'^title: "(.*)"$', source, re.M).group(1)
    body = re.sub(r"\A---\n.*?\n---\n", "", source, count=1, flags=re.S)
    # Preview DEV's documented details tag without a network call or Liquid runtime.
    assert body.count("{% details ") == body.count("{% enddetails %}")
    body = re.sub(r"\{% details (.+?) %\}",
                  lambda m: '<details markdown="1"><summary>' + html.escape(m.group(1)) + '</summary>', body)
    body = body.replace("{% enddetails %}", "</details>")
    body = markdown.markdown(body, extensions=["tables", "fenced_code", "md_in_html", "toc"])
    def embed(m):
        asset = path.parent / m.group(1)
        if not asset.is_file():
            raise FileNotFoundError(asset)
        return 'src="data:image/png;base64,' + base64.b64encode(asset.read_bytes()).decode() + '"'
    body = re.sub(r'src="(\.\./[^"]+)"', embed, body)
    page = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>''' + html.escape(title) + '''</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f3ef;color:#172b38;font:18px/1.75 Georgia,serif}
main{max-width:920px;margin:40px auto;padding:48px 54px;background:#fff;border:1px solid #e1e3df}
h1,h2,h3,th,.label,summary{font-family:system-ui,sans-serif}h1{font-size:42px;line-height:1.16;letter-spacing:-1.3px}
h2{font-size:26px;line-height:1.3;margin-top:48px}a{color:#076e72}p{margin:1.15em 0}
h3{font-size:23px;line-height:1.35;margin-top:36px}
h3[id="my-experiment-diary"]{padding-top:20px;border-top:3px solid #bfdacf}
details{margin:24px 0;border:1px solid #dce2ec;background:#f7f8fc;padding:14px 20px;border-radius:6px;font-size:16px}
summary{cursor:pointer;color:#3446a0;font-size:15px;font-weight:650;line-height:1.5}
details[open] summary{margin-bottom:18px}details p:last-child{margin-bottom:4px}
blockquote{margin:24px 0;padding:8px 24px;border-left:4px solid #0a8077;background:#f1f7f5}
pre{background:#f3f5f6;padding:20px;white-space:pre-wrap;overflow-wrap:anywhere;font-size:14px;line-height:1.6}
code{font-size:.85em;overflow-wrap:anywhere}img{display:block;width:100%;height:auto;margin:28px 0}
table{display:block;overflow-x:auto;border-collapse:collapse;width:100%;font:14px/1.5 system-ui,sans-serif;margin:24px 0}
th,td{border-bottom:1px solid #dde2e4;padding:10px 12px;text-align:left;vertical-align:top}th{background:#edf3f2}
.label{font-size:12px;letter-spacing:1.4px;color:#687681;text-transform:uppercase}
@media(max-width:650px){main{margin:0;padding:28px 20px;border:0}h1{font-size:32px}body{font-size:17px}}
</style><main><div class="label">Local draft · Kaggle Benchmarking Challenge</div><h1>''' + html.escape(title) + "</h1>" + body + "</main></html>"
    target = ROOT / "post" / "preview.html"
    target.write_text(page, encoding="utf-8")
    print(f"Wrote self-contained preview: {target}")


if __name__ == "__main__":
    main()

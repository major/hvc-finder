"""Build the HTML page for the HVC Finder web app."""

from jinja2 import Environment, FileSystemLoader

from hvc_finder.calculate import run

if __name__ == "__main__":
    df = run()
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("hvc.html")

    timestamps = sorted(df["timestamp"].unique(), reverse=True)[:20]

    rendered = template.render(timestamps=timestamps, df=df)
    with open("public/index.html", "w") as f:
        f.write(rendered)

    df.to_csv("public/hvc.csv", index=False)

# Documentation site

This site is independent of the repository README and requires only Python 3.9+
and the standard library. Edit `index.html`, `guide.html`, and `style.css` here.
The generator substitutes `{{BASE}}` and `{{REPO}}`; do not hardcode a
root-relative asset or documentation link in a template.

Build for the project URL `https://miyako.github.io/uzu/`:

```sh
python3 site/build.py
python3 -m unittest discover -s tests -p test_site.py -v
```

Generated files live in the ignored `site/_site/` directory. For a root-mounted
local preview instead:

```sh
python3 site/build.py --base-path /
python3 -m http.server 8000 --directory site/_site
```

Visit `http://localhost:8000/`. Rebuild without `--base-path /` before serving
at the project URL. Tests also restore the `/uzu/` build after testing an
alternate base.

## Deployment

The `Deploy documentation` workflow tests and builds on relevant pushes and
manual dispatches, but only on the repository's default branch. It uploads
the static output and deploys using the `github-pages` environment. A
repository administrator must select **GitHub Actions** as the Pages source
in **Settings → Pages**, and allow deployments from the default branch in
any environment protection rules. This change does not modify those remote
settings or start a deployment.

Only the deployment job receives `pages: write` and `id-token: write`; the
build uses read-only repository permissions. No Jekyll, Ruby, JavaScript,
third-party fonts, CDN, or runtime network dependency is used.

Internal generated links and fragments are checked locally. External links
(including the repository's native build guide) are not fetched by the tests.

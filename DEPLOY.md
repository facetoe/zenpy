# Deploying Instructions

Releases are published to PyPI automatically by
[`.github/workflows/publish.yml`](.github/workflows/publish.yml) whenever a
full (non pre-release) GitHub Release is published - marking a release as
a pre-release will *not* trigger it. To cut a release:

1. Bump the version in `zenpy/__init__.py` (`__version__`) and `setup.py`
   (`version` and `download_url`).
2. If you bumped the agent version above, likely we'll need to generate new
   wires from betamax.
3. Commit the version bump and merge it to `master`.
4. Tag the commit with the new version number (no `v` prefix, e.g. `2.0.58`)
   and push the tag.
5. Create a GitHub Release from that tag and publish it
   (https://github.com/facetoe/zenpy/releases/new). Leave "Set as a
   pre-release" unchecked - a pre-release will not trigger publishing.
   (Editing an existing pre-release to unmark it as a pre-release also
   triggers publishing, per GitHub's semantics for release events - so
   don't do that unless you actually mean to publish it.)
6. Check the Actions tab for the `publish.yml` run, and confirm the new
   version shows up at https://pypi.org/project/zenpy/ - the Release page
   itself doesn't reflect whether the PyPI upload succeeded.

Publishing the release triggers the `publish.yml` workflow, which builds the
sdist/wheel and uploads them to PyPI. The workflow fails if the tag doesn't
match the version in *both* `zenpy/__init__.py` and `setup.py`, so step 1
must happen before tagging.

## One-time setup (PyPI project owner only)

The workflow publishes via [PyPI Trusted
Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC), so no PyPI API
token needs to be stored as a GitHub secret. Before the first automated
release, a `zenpy` project owner needs to add a publisher at
https://pypi.org/manage/project/zenpy/settings/publishing/ with the exact
values in `publish.yml`'s header comment (owner, repository, workflow
filename, environment) - see that file rather than duplicating them here.

## Manual fallback

The automated workflow above is now the intended path. If it's broken and
you need to publish manually, you'll first need to create your own PyPI API
token (Trusted Publishing only authorizes GitHub Actions, not local
`twine`), then:

```
make clean
pip install build twine
python -m build
twine upload dist/*
```

This skips the tag/version consistency check the workflow performs, so
double-check `zenpy/__init__.py` and `setup.py` agree before uploading.

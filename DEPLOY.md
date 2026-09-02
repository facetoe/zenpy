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

Publishing the release triggers the `publish.yml` workflow, which builds the
sdist/wheel and uploads them to PyPI. The workflow fails if the tag doesn't
match `zenpy/__init__.py`'s `__version__`, so step 1 must happen before
tagging.

## One-time setup (PyPI project owner only)

The workflow publishes via [PyPI Trusted
Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC), so no PyPI API
token needs to be stored as a GitHub secret. Before the first automated
release, a `zenpy` project owner needs to add a publisher at
https://pypi.org/manage/project/zenpy/settings/publishing/ with:

- Owner: `facetoe`
- Repository: `zenpy`
- Workflow: `publish.yml`
- Environment: leave blank

## Manual fallback

If you need to publish manually instead:

```
make clean
pip install build
python -m build
twine upload dist/*
```

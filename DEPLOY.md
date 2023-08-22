# Deploying Instructions
1. Bump all versions including optional (affects tests) https://github.com/facetoe/zenpy/blob/a3d7d3e49096f0bde67c85d6f227ed8db7469c63/zenpy/__init__.py#L61-L60
2. If you bump the agent version above, likely we'll need to generate new wires from betamax
2. git pull into clean area (after bumping new version and tagging release and updating toml file)
2. make clean 
3. python setup.py sdist
4. twine upload dist/*

#! /bin/sh

# Development only

wget https://raw.githubusercontent.com/andrey-pohilko/registry-cli/master/requirements-build.txt
wget https://raw.githubusercontent.com/andrey-pohilko/registry-cli/master/registry.py
sed -i -E 's|try_oauth = requests\.post\(request_url, auth=auth, \*\*kwargs\)|try_oauth = requests\.get\(request_url, auth=auth, \*\*kwargs\)|g' ./registry.py

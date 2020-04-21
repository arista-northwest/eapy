.PHONY: docs

init:
	pip3 install pipenv --upgrade
	pipenv install --dev

test:
	pipenv run coverage run -m pytest test_eapi.py

publish:
	pip3 install 'twine>=1.5.0'
	python3 setup.py sdist bdist_wheel
	twine upload dist/*
	rm -fr build dist .egg gnmi-py.egg-info

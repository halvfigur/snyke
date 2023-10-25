typecheck:
	mypy . --check-untyped-defs

requirements:
	pip3 freeze > requirements.txt

run:
	python3 ./main.py


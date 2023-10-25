typecheck:
	mypy . --check-untyped-defs

requirements:
	pip3 freeze > requirements.txt

format:
	python3 -m black snyke
run:
	python3 ./main.py


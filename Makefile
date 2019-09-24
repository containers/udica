.PHONY: install
install:
	python3 setup.py install

.PHONY: test
test:
	python3 -m unittest -v tests/test_main.py

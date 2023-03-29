TAG ?= latest
IMAGE_NAME ?= udica
CONTAINER_CMD ?= podman

.PHONY: install
install:
	python3 setup.py install

.PHONY:
lint:
	pyflakes udica

.PHONY:
format:
	black *.py udica/*.py tests/*.py

.PHONY:
format-check:
	black --check --diff *.py udica/*.py tests/*.py

.PHONY: test
test: lint format-check
	python3 -m unittest -v tests/test_unit.py

.PHONY: image
image:
	$(CONTAINER_CMD) build -f Dockerfile -t $(IMAGE_NAME):$(TAG)

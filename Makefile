TAG ?= latest
IMAGE_NAME ?= udica
CONTAINER_CMD ?= podman

.PHONY: install
install:
	python3 setup.py install

.PHONY:
lint:
	pyflakes udica

.PHONY: test
test: lint
	python3 -m unittest -v tests/test_unit.py

.PHONY: image
image:
	$(CONTAINER_CMD) build -f Dockerfile -t $(IMAGE_NAME):$(TAG)

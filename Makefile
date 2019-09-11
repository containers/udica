TAG ?= latest
IMAGE_NAME ?= udica
CONTAINER_CMD ?= podman

.PHONY: install
install:
	python3 setup.py install

.PHONY: test
test:
	python3 -m unittest -v tests/test_unit.py

.PHONY: image
image:
	$(CONTAINER_CMD) build -f Dockerfile -t $(IMAGE_NAME):$(TAG)

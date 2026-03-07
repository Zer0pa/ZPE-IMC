ROOT_DIR := $(CURDIR)

.PHONY: bootstrap test build demo comet-run determinism-probe voice-tools-smoke benchmark clean portability-lint

bootstrap test build demo comet-run determinism-probe voice-tools-smoke benchmark clean:
	$(MAKE) -C "$(ROOT_DIR)/executable" $@

portability-lint:
	@if rg -n --no-heading -S '/Users/[A-Za-z0-9._ -]+|[A-Za-z]:\\\\' \
		README.md ROADMAP.md CHANGELOG.md CITATION.cff \
		docs code/README.md code/wasm/README.md code/deployment/triton/model_repository/README.md \
		proofs/*.md proofs/runbooks/*.md \
		-g '*.md' -g '*.cff'; then \
		echo 'portability-lint: FAIL (machine-absolute path residue found)'; \
		exit 1; \
	else \
		echo 'portability-lint: PASS'; \
	fi

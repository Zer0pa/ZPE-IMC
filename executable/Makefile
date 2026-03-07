PYTHON ?= python3
V0_DIR := ..
CODE_DIR := ../code
VENV_DIR := ../.venv
VENV_PYTHON := ../.venv/bin/python
VENV_PIP := ../.venv/bin/pip
RUN_PYTHON := $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),$(PYTHON))
PYTHONPATH_CODE_DIR := PYTHONPATH=".:$$PYTHONPATH"
PYTHONPATH_EXEC_DIR := PYTHONPATH="../code:$$PYTHONPATH"
BASE_EXTRAS ?= dev,full
OPTIONAL_EXTRAS ?=
INSTALL_EXTRAS := $(BASE_EXTRAS)
ifneq ($(strip $(OPTIONAL_EXTRAS)),)
INSTALL_EXTRAS := $(BASE_EXTRAS),$(OPTIONAL_EXTRAS)
endif

.PHONY: bootstrap test build demo comet-run determinism-probe voice-tools-smoke benchmark clean

bootstrap:
	"$(PYTHON)" -m venv "$(VENV_DIR)"
	"$(VENV_PIP)" install --upgrade pip
	"$(VENV_PIP)" install build pytest
	"$(VENV_PIP)" install -e "$(CODE_DIR)[$(INSTALL_EXTRAS)]"

test:
	cd "$(CODE_DIR)" && $(PYTHONPATH_CODE_DIR) STROKEGRAM_ENABLE_DIAGRAM=1 STROKEGRAM_ENABLE_MUSIC=1 STROKEGRAM_ENABLE_VOICE=1 "$(RUN_PYTHON)" -m pytest tests tests_phase3 -q

build:
	cd "$(CODE_DIR)" && $(PYTHONPATH_CODE_DIR) "$(RUN_PYTHON)" -m build

demo:
	$(PYTHONPATH_EXEC_DIR) STROKEGRAM_ENABLE_DIAGRAM=1 STROKEGRAM_ENABLE_MUSIC=1 STROKEGRAM_ENABLE_VOICE=1 "$(RUN_PYTHON)" "./demo.py"

comet-run:
	$(PYTHONPATH_EXEC_DIR) "$(RUN_PYTHON)" "./run_with_comet.py"

determinism-probe:
	$(PYTHONPATH_EXEC_DIR) "$(RUN_PYTHON)" "./determinism_probe.py" --runs 5

voice-tools-smoke:
	$(PYTHONPATH_EXEC_DIR) "$(RUN_PYTHON)" "./voice_groundtruth_optional_tools.py" smoke --json

benchmark:
	cd "$(CODE_DIR)" && $(PYTHONPATH_CODE_DIR) PYTHONHASHSEED=0 STROKEGRAM_ENABLE_DIAGRAM=1 STROKEGRAM_ENABLE_MUSIC=1 STROKEGRAM_ENABLE_VOICE=1 "$(RUN_PYTHON)" ./benchmarks/run_benchmarks.py --run-id "$${WP_C_BENCH_RUN_ID:-WP-C-BENCH-DET}" --scenario-dir ./benchmarks/scenarios --artifact-root "$${WP_C_BENCH_ART_ROOT:-./benchmarks/artifacts/wp_c}" --output-dir "$${WP_C_BENCH_METRICS_DIR:-./benchmarks/artifacts/wp_c/metrics}" --profile-top 10

clean:
	"$(PYTHON)" "./cleanup_artifacts.py" --root "$(V0_DIR)"

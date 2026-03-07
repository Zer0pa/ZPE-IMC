from __future__ import annotations

from dataclasses import dataclass, field
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

from zpe_multimodal import ZPETokenizer
from zpe_multimodal import __version__ as ZPE_VERSION

ADAPTER_VERSION = "1.0.0"
TOKENIZER_CONFIG_NAME = "tokenizer_config.json"
SPECIAL_TOKENS_MAP_NAME = "special_tokens_map.json"
ZPE_TOKENIZER_CONFIG_NAME = "zpe_tokenizer_config.json"


class MissingOptionalDependencyError(RuntimeError):
    """Raised when an optional adapter dependency is not installed."""


@dataclass(frozen=True)
class HFTokenizerMetadata:
    """Persisted metadata stored alongside local/Hub-pretrained artifacts."""

    tokenizer_type: str = "zpe-multimodal"
    zpe_multimodal_version: str = ZPE_VERSION
    adapter_version: str = ADAPTER_VERSION
    lattice_path: str | None = None
    ref: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "tokenizer_type": self.tokenizer_type,
            "zpe_multimodal_version": self.zpe_multimodal_version,
            "adapter_version": self.adapter_version,
            "lattice_path": self.lattice_path,
            "ref": self.ref,
            "extras": self.extras,
        }
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "HFTokenizerMetadata":
        return cls(
            tokenizer_type=str(payload.get("tokenizer_type", "zpe-multimodal")),
            zpe_multimodal_version=str(payload.get("zpe_multimodal_version", ZPE_VERSION)),
            adapter_version=str(payload.get("adapter_version", ADAPTER_VERSION)),
            lattice_path=(str(payload["lattice_path"]) if payload.get("lattice_path") else None),
            ref=(str(payload["ref"]) if payload.get("ref") else None),
            extras=dict(payload.get("extras", {})),
        )


def _missing_dependency_message() -> str:
    return (
        "HuggingFace adapter requires optional dependency 'transformers'. "
        "Install with: pip install -e '.[hf]'"
    )


def _is_transformers_available() -> bool:
    return importlib.util.find_spec("transformers") is not None


def require_transformers() -> None:
    """Raise an actionable error when the optional transformers stack is unavailable."""
    if not _is_transformers_available():
        raise MissingOptionalDependencyError(_missing_dependency_message())


def _normalize_ids(ids: Sequence[int] | Iterable[int]) -> list[int]:
    normalized: list[int] = []
    for idx, token in enumerate(ids):
        if isinstance(token, bool) or not isinstance(token, int):
            raise TypeError(f"token_ids[{idx}] must be int, got {type(token).__name__}")
        normalized.append(int(token))
    return normalized


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class HuggingFaceZPEAdapter:
    """Lightweight HuggingFace-style tokenizer wrapper for ZPE tokenization."""

    model_input_names = ["input_ids", "attention_mask"]

    def __init__(
        self,
        tokenizer: ZPETokenizer | None = None,
        metadata: HFTokenizerMetadata | None = None,
        model_max_length: int = 1_000_000,
    ) -> None:
        derived_lattice_path = None
        if tokenizer is not None:
            derived_lattice_path = getattr(tokenizer, "lattice_path", None)

        if metadata is None:
            metadata = HFTokenizerMetadata(lattice_path=derived_lattice_path)

        if tokenizer is None and metadata.lattice_path:
            lattice_path = Path(metadata.lattice_path).expanduser()
            if lattice_path.exists() and lattice_path.is_file():
                tokenizer = ZPETokenizer.from_lattice(str(lattice_path))

        self._tokenizer = tokenizer or ZPETokenizer()
        self.metadata = metadata
        self.model_max_length = int(model_max_length)

    @property
    def tokenizer(self) -> ZPETokenizer:
        return self._tokenizer

    def encode(self, text: str, add_special_tokens: bool = False, **_: Any) -> list[int]:
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        if add_special_tokens:
            # No special-token vocabulary is defined in ZPE base tokenizer.
            return self._tokenizer.encode(text)
        return self._tokenizer.encode(text)

    def decode(self, token_ids: Sequence[int] | Iterable[int], skip_special_tokens: bool = True, **_: Any) -> str:
        _ = skip_special_tokens
        return self._tokenizer.decode(_normalize_ids(token_ids))

    def __call__(self, text: str, add_special_tokens: bool = False, return_tensors: str | None = None, **_: Any) -> dict[str, Any]:
        input_ids = self.encode(text, add_special_tokens=add_special_tokens)
        attention_mask = [1] * len(input_ids)

        if return_tensors is None:
            return {"input_ids": input_ids, "attention_mask": attention_mask}

        if return_tensors in {"np", "numpy"}:
            import numpy as np

            return {
                "input_ids": np.array([input_ids], dtype=np.int64),
                "attention_mask": np.array([attention_mask], dtype=np.int64),
            }

        if return_tensors in {"pt", "torch"}:
            try:
                import torch
            except ModuleNotFoundError as exc:
                raise MissingOptionalDependencyError(
                    "Torch tensors requested but torch is not installed. Install torch or omit return_tensors='pt'."
                ) from exc
            return {
                "input_ids": torch.tensor([input_ids], dtype=torch.long),
                "attention_mask": torch.tensor([attention_mask], dtype=torch.long),
            }

        raise ValueError("return_tensors must be one of: None, 'np', 'numpy', 'pt', 'torch'")

    def batch_decode(
        self,
        sequences: Sequence[Sequence[int]] | Iterable[Sequence[int]],
        skip_special_tokens: bool = True,
        **_: Any,
    ) -> list[str]:
        return [self.decode(seq, skip_special_tokens=skip_special_tokens) for seq in sequences]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tokenizer_class": self.__class__.__name__,
            "tokenizer_type": "zpe-multimodal",
            "model_max_length": self.model_max_length,
            "zpe_metadata": self.metadata.to_dict(),
        }

    def save_pretrained(
        self,
        save_directory: str | Path,
        push_to_hub: bool = False,
        repo_id: str | None = None,
        token: str | None = None,
        private: bool | None = None,
        **_: Any,
    ) -> tuple[str, ...]:
        save_dir = Path(save_directory).expanduser().resolve()
        save_dir.mkdir(parents=True, exist_ok=True)

        tokenizer_config = {
            "tokenizer_class": self.__class__.__name__,
            "tokenizer_type": "zpe-multimodal",
            "model_max_length": self.model_max_length,
            "clean_up_tokenization_spaces": False,
            "zpe_metadata": self.metadata.to_dict(),
        }
        zpe_config = {
            "schema_version": 1,
            "metadata": self.metadata.to_dict(),
            "model_max_length": self.model_max_length,
        }

        tokenizer_config_path = save_dir / TOKENIZER_CONFIG_NAME
        special_tokens_path = save_dir / SPECIAL_TOKENS_MAP_NAME
        zpe_config_path = save_dir / ZPE_TOKENIZER_CONFIG_NAME

        _write_json(tokenizer_config_path, tokenizer_config)
        _write_json(special_tokens_path, {})
        _write_json(zpe_config_path, zpe_config)

        if push_to_hub:
            if not repo_id or not repo_id.strip():
                raise ValueError("repo_id is required when push_to_hub=True")
            try:
                from huggingface_hub import HfApi
            except ModuleNotFoundError as exc:
                raise MissingOptionalDependencyError(
                    "push_to_hub requires 'huggingface_hub'. Install with: pip install -e '.[hf]'"
                ) from exc

            api = HfApi(token=token)
            api.create_repo(repo_id=repo_id, exist_ok=True, repo_type="model", private=private)
            api.upload_folder(repo_id=repo_id, folder_path=str(save_dir), repo_type="model")

        return (str(tokenizer_config_path), str(special_tokens_path), str(zpe_config_path))

    @classmethod
    def from_pretrained(
        cls,
        pretrained_model_name_or_path: str | Path,
        local_files_only: bool = False,
        revision: str | None = None,
        token: str | None = None,
        **_: Any,
    ) -> "HuggingFaceZPEAdapter":
        model_ref = str(pretrained_model_name_or_path)
        local_path = Path(model_ref).expanduser()

        if local_path.exists():
            if local_path.is_file():
                local_dir = local_path.parent
            else:
                local_dir = local_path
            tokenizer_config = _read_json(local_dir / TOKENIZER_CONFIG_NAME)
            zpe_config = _read_json(local_dir / ZPE_TOKENIZER_CONFIG_NAME)
            metadata_payload = zpe_config.get("metadata") or tokenizer_config.get("zpe_metadata") or {}
            metadata = HFTokenizerMetadata.from_dict(dict(metadata_payload))
            model_max_length = int(tokenizer_config.get("model_max_length", zpe_config.get("model_max_length", 1_000_000)))
            return cls(metadata=metadata, model_max_length=model_max_length)

        if local_files_only:
            raise FileNotFoundError(f"Local pretrained path not found: {model_ref}")

        try:
            from huggingface_hub import hf_hub_download
        except ModuleNotFoundError as exc:
            raise MissingOptionalDependencyError(
                "Remote from_pretrained requires 'huggingface_hub'. Install with: pip install -e '.[hf]'"
            ) from exc

        tokenizer_config_path = Path(
            hf_hub_download(
                repo_id=model_ref,
                filename=TOKENIZER_CONFIG_NAME,
                revision=revision,
                token=token,
            )
        )
        try:
            zpe_config_path = Path(
                hf_hub_download(
                    repo_id=model_ref,
                    filename=ZPE_TOKENIZER_CONFIG_NAME,
                    revision=revision,
                    token=token,
                )
            )
            zpe_config = _read_json(zpe_config_path)
        except Exception:
            zpe_config = {}

        tokenizer_config = _read_json(tokenizer_config_path)
        metadata_payload = zpe_config.get("metadata") or tokenizer_config.get("zpe_metadata") or {}
        metadata = HFTokenizerMetadata.from_dict(dict(metadata_payload))
        model_max_length = int(tokenizer_config.get("model_max_length", zpe_config.get("model_max_length", 1_000_000)))
        return cls(metadata=metadata, model_max_length=model_max_length)


def as_huggingface(ref: str | None = None) -> HuggingFaceZPEAdapter:
    """Factory-style helper expected by downstream adapter surfaces."""
    if ref:
        return HuggingFaceZPEAdapter.from_pretrained(ref)
    return HuggingFaceZPEAdapter()


__all__ = [
    "ADAPTER_VERSION",
    "HFTokenizerMetadata",
    "HuggingFaceZPEAdapter",
    "MissingOptionalDependencyError",
    "as_huggingface",
    "require_transformers",
]

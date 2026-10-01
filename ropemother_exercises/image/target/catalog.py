#!/usr/bin/env python3
# ropemother_exercises/image/target/catalog.py

"""Catalog and resolution for supported reconstruction targets."""

import dataclasses
import hashlib
import random

from ropemother_exercises.image.events import TargetKey
from ropemother_exercises.image.exceptions import TargetCatalogError
from ropemother_exercises.image.target.bitmap_assets import (
    load_prepared_bitmap_sources,
)
from ropemother_exercises.image.target.generator import (
    diagnostic_x_target_bitmap,
    egg_shell_target_bitmap,
    prepared_target_bitmap,
    rock_matrix_target_bitmap,
)
from ropemother_exercises.image.target.hidden import HiddenTarget
from ropemother_exercises.image.tomography.images import Bitmap

_TARGET_KEY_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"

_DIAGNOSTIC_KEY_PREFIX = "a"
_BARE_PREPARED_KEY_PREFIX = "b"
_HULLED_PREPARED_KEY_PREFIX = "c"

_DIAGNOSTIC_TARGETS = {
    TargetKey("a000"): diagnostic_x_target_bitmap,
}

_BARE_PREPARED_SOURCE_WIDTH = 3
_HULLED_KEY_BODY_LENGTH = 8

_EGG_SHELL_FORM = 0
_ROCK_MATRIX_FORM = 1
_HULL_FORMS = (
    _EGG_SHELL_FORM,
    _ROCK_MATRIX_FORM,
)
_HULLED_VARIATION_COUNT = 256


@dataclasses.dataclass(frozen=True, kw_only=True)
class ResolvedTarget:
    key: TargetKey
    target: HiddenTarget


@dataclasses.dataclass(frozen=True, kw_only=True)
class _HulledTargetRealization:
    source_index: int
    hull_form: int
    variation: int


def choose_target() -> ResolvedTarget:
    rng = random.SystemRandom()
    body = "".join(
        rng.choices(_TARGET_KEY_ALPHABET, k=_HULLED_KEY_BODY_LENGTH)
    )
    checksum = _target_key_checksum(f"prepared-hulled-v2:{body}")
    key = TargetKey(f"{_HULLED_PREPARED_KEY_PREFIX}{body}{checksum}")
    return resolve_target(key)


def parse_target_key(value: str) -> TargetKey:
    key = TargetKey(value)
    prefix = key[:1]

    if prefix == _DIAGNOSTIC_KEY_PREFIX:
        if key not in _DIAGNOSTIC_TARGETS:
            raise TargetCatalogError(f"unknown diagnostic target key: {key}")
    elif prefix == _BARE_PREPARED_KEY_PREFIX:
        _bare_source_index(key)
    elif prefix == _HULLED_PREPARED_KEY_PREFIX:
        _hulled_target_realization(key)
    else:
        raise TargetCatalogError(f"unknown target key: {key}")

    return key


def resolve_target(key: TargetKey) -> ResolvedTarget:
    prefix = key[:1]

    if prefix == _DIAGNOSTIC_KEY_PREFIX:
        bitmap_factory = _DIAGNOSTIC_TARGETS.get(key)

        if bitmap_factory is None:
            raise TargetCatalogError(f"unknown diagnostic target key: {key}")

        bitmap = bitmap_factory()
    elif prefix == _BARE_PREPARED_KEY_PREFIX:
        source_index = _bare_source_index(key)
        bitmap = prepared_target_bitmap(source_index)
    elif prefix == _HULLED_PREPARED_KEY_PREFIX:
        realization = _hulled_target_realization(key)
        bitmap = _hulled_target_bitmap(realization)
    else:
        raise TargetCatalogError(f"unknown target key: {key}")

    return ResolvedTarget(key=key, target=HiddenTarget(bitmap))


def bare_prepared_target_key(key: TargetKey) -> TargetKey | None:
    prefix = key[:1]

    if prefix == _DIAGNOSTIC_KEY_PREFIX:
        if key not in _DIAGNOSTIC_TARGETS:
            raise TargetCatalogError(f"unknown diagnostic target key: {key}")

        bare_key = None
    elif prefix == _BARE_PREPARED_KEY_PREFIX:
        _bare_source_index(key)
        bare_key = key
    elif prefix == _HULLED_PREPARED_KEY_PREFIX:
        realization = _hulled_target_realization(key)
        source_code = _encode_base32(
            realization.source_index, width=_BARE_PREPARED_SOURCE_WIDTH
        )
        bare_key = TargetKey(f"{_BARE_PREPARED_KEY_PREFIX}{source_code}")
    else:
        raise TargetCatalogError(f"unknown target key: {key}")

    return bare_key


def target_source_description(key: TargetKey) -> str:
    prefix = key[:1]

    if prefix == _DIAGNOSTIC_KEY_PREFIX:
        if key not in _DIAGNOSTIC_TARGETS:
            raise TargetCatalogError(f"unknown diagnostic target key: {key}")

        description = "Diagnostic X"
    elif prefix == _BARE_PREPARED_KEY_PREFIX:
        source_index = _bare_source_index(key)
        description = _prepared_source_description(source_index)
    elif prefix == _HULLED_PREPARED_KEY_PREFIX:
        realization = _hulled_target_realization(key)
        description = _prepared_source_description(realization.source_index)
    else:
        raise TargetCatalogError(f"unknown target key: {key}")

    return description


def _bare_source_index(key: TargetKey) -> int:
    expected_length = _BARE_PREPARED_SOURCE_WIDTH + 1

    if len(key) != expected_length:
        raise TargetCatalogError(f"invalid bare prepared target key: {key}")

    source_index = _decode_base32(key[1:])
    sources = load_prepared_bitmap_sources()

    if source_index >= len(sources):
        raise TargetCatalogError(f"unknown bare prepared target key: {key}")

    return source_index


def _decode_base32(value: str) -> int:
    result = 0

    for character in value:
        try:
            digit = _TARGET_KEY_ALPHABET.index(character)
        except ValueError as error:
            raise TargetCatalogError(
                "target key contains an invalid character"
            ) from error
        result = result * len(_TARGET_KEY_ALPHABET) + digit

    return result


def _encode_base32(value: int, *, width: int) -> str:
    digits = []

    for _ in range(width):
        value, digit = divmod(value, len(_TARGET_KEY_ALPHABET))
        digits.append(_TARGET_KEY_ALPHABET[digit])

    if value != 0:
        raise TargetCatalogError("target key value exceeds field width")

    return "".join(reversed(digits))


def _prepared_source_description(source_index: int) -> str:
    sources = load_prepared_bitmap_sources()
    return sources[source_index].description


def _hulled_target_bitmap(realization: _HulledTargetRealization) -> Bitmap:
    if realization.hull_form == _EGG_SHELL_FORM:
        bitmap = egg_shell_target_bitmap(
            realization.source_index,
            realization.variation,
        )
    else:
        bitmap = rock_matrix_target_bitmap(
            realization.source_index,
            realization.variation,
        )

    return bitmap


def _hulled_target_realization(key: TargetKey) -> _HulledTargetRealization:
    expected_length = _HULLED_KEY_BODY_LENGTH + 2

    if len(key) != expected_length:
        raise TargetCatalogError(f"invalid hulled prepared target key: {key}")

    body = key[1:-1]

    if any(character not in _TARGET_KEY_ALPHABET for character in body):
        raise TargetCatalogError("target key contains an invalid character")

    expected_checksum = _target_key_checksum(f"prepared-hulled-v2:{body}")

    if key[-1] != expected_checksum:
        raise TargetCatalogError(f"invalid hulled prepared target key: {key}")

    sources = load_prepared_bitmap_sources()

    if not sources:
        raise TargetCatalogError("prepared target catalog is empty")

    rng = random.Random(body)
    source_index = rng.randrange(len(sources))
    hull_form = rng.choice(_HULL_FORMS)
    variation = rng.randrange(_HULLED_VARIATION_COUNT)
    hull_target = _HulledTargetRealization(
        source_index=source_index, hull_form=hull_form, variation=variation
    )
    return hull_target


def _target_key_checksum(document: str) -> str:
    digest = hashlib.sha256(document.encode("utf-8")).digest()
    return _TARGET_KEY_ALPHABET[digest[0] & 31]

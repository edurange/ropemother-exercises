#!/usr/bin/env python3
# ropemother_exercises/image/target/catalog.py

"""Stable identities and resolution for supported reconstruction targets."""

import collections.abc
import dataclasses
import hashlib
import json
import random

from ropemother_exercises.image.events import TargetKey
from ropemother_exercises.image.exceptions import TargetCatalogError
from ropemother_exercises.image.target.generator import (
    tutorial_target_bitmap_from_asset,
)
from ropemother_exercises.image.target.hidden import HiddenTarget

type _TargetKeyValidator = collections.abc.Callable[[TargetKey], None]
type _TargetResolver = collections.abc.Callable[[TargetKey], HiddenTarget]

_PREPARED_BITMAP_KEY_PREFIX = "a"
_TARGET_KEY_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"
_DEFAULT_TARGET_KEY_BODY_LENGTH = 7


@dataclasses.dataclass(frozen=True, kw_only=True)
class ResolvedTarget:
    key: TargetKey
    target: HiddenTarget


@dataclasses.dataclass(frozen=True, kw_only=True)
class _TargetFamily:
    validate_key: _TargetKeyValidator
    resolve: _TargetResolver


@dataclasses.dataclass(frozen=True, kw_only=True)
class _PreparedTargetSpecification:
    asset_id: str
    seed: int
    key_body_length: int = _DEFAULT_TARGET_KEY_BODY_LENGTH


def choose_target() -> ResolvedTarget:
    keys = tuple(_PREPARED_TARGET_SPECIFICATIONS_BY_KEY)
    return resolve_target(random.SystemRandom().choice(keys))


def parse_target_key(value: str) -> TargetKey:
    key = TargetKey(value)
    family = _target_family(key)
    family.validate_key(key)
    return key


def resolve_target(key: TargetKey) -> ResolvedTarget:
    family = _target_family(key)
    family.validate_key(key)
    target = family.resolve(key)
    return ResolvedTarget(key=key, target=target)


def _target_key_body(document: str, length: int) -> str:
    digest = hashlib.sha256(document.encode("utf-8")).digest()
    bit_count = length * 5
    value = int.from_bytes(digest, "big") >> (len(digest) * 8 - bit_count)
    shifts = range(bit_count - 5, -1, -5)
    alphabet = _TARGET_KEY_ALPHABET
    return "".join(alphabet[(value >> shift) & 31] for shift in shifts)


def _prepared_target_key(
    specification: _PreparedTargetSpecification,
) -> TargetKey:
    record = {
        "scheme": "prepared-bitmap-v1",
        "asset_id": specification.asset_id,
        "seed": specification.seed,
    }
    document = json.dumps(record, sort_keys=True, separators=(",", ":"))
    body = _target_key_body(document, specification.key_body_length)
    return TargetKey(f"{_PREPARED_BITMAP_KEY_PREFIX}{body}")


_PREPARED_TARGET_SPECIFICATIONS = (
    _PreparedTargetSpecification(
        asset_id="Software_Warning_Sign_Circle_Question_Mark_Help", seed=101
    ),
    _PreparedTargetSpecification(asset_id="Travel_Ship_Anchor_Navy", seed=103),
    _PreparedTargetSpecification(
        asset_id="RPG_Stat_HP_Health_Heart", seed=109
    ),
    _PreparedTargetSpecification(
        asset_id="Boardgames_Chess_Piece_Knight_Big", seed=113
    ),
    _PreparedTargetSpecification(
        asset_id="Weather_Moon_Night_Crescent_Darkness_Mode_Twilight_Big",
        seed=127,
    ),
    _PreparedTargetSpecification(
        asset_id="Map_Markers_Tree_Forest_Pine", seed=131
    ),
    _PreparedTargetSpecification(
        asset_id="Travel_Ship_Sailing_Boat", seed=139
    ),
    _PreparedTargetSpecification(
        asset_id="Tools_Crafting_Key_Unlock_2", seed=149
    ),
    _PreparedTargetSpecification(
        asset_id="Weather_Thunderstorm_Cloud_Lightning_Zap", seed=157
    ),
    _PreparedTargetSpecification(
        asset_id="Travel_UFO_Alien_Spaceship", seed=163
    ),
)
_PREPARED_TARGET_SPECIFICATIONS_BY_KEY = {
    _prepared_target_key(specification): specification
    for specification in _PREPARED_TARGET_SPECIFICATIONS
}

if len(_PREPARED_TARGET_SPECIFICATIONS_BY_KEY) != len(
    _PREPARED_TARGET_SPECIFICATIONS
):
    raise TargetCatalogError("prepared target keys are not unique")


def _validate_prepared_target_key(key: TargetKey) -> None:
    if key not in _PREPARED_TARGET_SPECIFICATIONS_BY_KEY:
        raise TargetCatalogError(f"unknown prepared target key: {key}")


def _resolve_prepared_target(key: TargetKey) -> HiddenTarget:
    specification = _PREPARED_TARGET_SPECIFICATIONS_BY_KEY[key]
    bitmap = tutorial_target_bitmap_from_asset(
        specification.asset_id, specification.seed
    )
    return HiddenTarget(bitmap)


_TARGET_FAMILIES = {
    _PREPARED_BITMAP_KEY_PREFIX: _TargetFamily(
        validate_key=_validate_prepared_target_key,
        resolve=_resolve_prepared_target,
    ),
}


def _target_family(key: TargetKey) -> _TargetFamily:
    key_prefix = key[:1]
    family = _TARGET_FAMILIES.get(key_prefix)

    if family is None:
        raise TargetCatalogError(f"unknown target key: {key}")

    return family

"""Allways Data Access Service (DAS) — swap lookup when resolved data is off-chain.

Environment:
    ALLWAYS_DAS_BASE_URL — Base URL for the indexer API (default: test-api.all-ways.io).
"""

from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

import requests

from allways.chains import SUPPORTED_CHAINS
from allways.classes import Swap, SwapStatus

DEFAULT_DAS_BASE_URL = 'https://test-api.all-ways.io'
_DAS_HEADERS = {'Accept': 'application/json'}

_DAS_STATUS = {
    'ACTIVE': SwapStatus.ACTIVE,
    'FULFILLED': SwapStatus.FULFILLED,
    'COMPLETED': SwapStatus.COMPLETED,
    'TIMED_OUT': SwapStatus.TIMED_OUT,
}


def get_das_base_url() -> str:
    return os.environ.get('ALLWAYS_DAS_BASE_URL', DEFAULT_DAS_BASE_URL).rstrip('/')


def _str_field(value: Any) -> str:
    if value is None:
        return ''
    return str(value)


def _int_field(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    s = str(value).strip()
    if not s:
        return 0
    return int(s)


def _tao_decimal_to_rao(tao_decimal: str) -> int:
    try:
        return int(Decimal(tao_decimal.strip()) * Decimal(10**9))
    except (InvalidOperation, AttributeError, TypeError, ValueError):
        return 0


def swap_from_das(raw: dict[str, Any], *, fallback_swap_id: int = 0) -> Swap:
    """Build a contract-shaped Swap from a DAS `/swaps/{id}` swap object."""
    st = str(raw.get('status') or '').upper()
    status = _DAS_STATUS.get(st, SwapStatus.ACTIVE)
    swap_id = _int_field(raw.get('swapId')) or fallback_swap_id
    tao_raw = raw.get('taoAmount')
    if isinstance(tao_raw, str):
        tao_rao = _tao_decimal_to_rao(tao_raw)
    else:
        tao_rao = _int_field(tao_raw)
    rate_val = raw.get('rate')
    rate_str = str(rate_val) if rate_val is not None else ''

    return Swap(
        id=swap_id,
        user_hotkey=_str_field(raw.get('userAddress')),
        miner_hotkey=_str_field(raw.get('minerHotkey')),
        source_chain=_str_field(raw.get('sourceChain')).lower(),
        dest_chain=_str_field(raw.get('destChain')).lower(),
        source_amount=_int_field(raw.get('sourceAmount')),
        dest_amount=_int_field(raw.get('destAmount')),
        tao_amount=tao_rao,
        user_source_address=_str_field(raw.get('userSourceAddress')),
        user_dest_address=_str_field(raw.get('userDestAddress')),
        miner_source_address=_str_field(raw.get('minerSourceAddress')),
        miner_dest_address=_str_field(raw.get('minerDestAddress')),
        rate=rate_str,
        source_tx_hash=_str_field(raw.get('sourceTxHash')),
        dest_tx_hash=_str_field(raw.get('destTxHash')),
        status=status,
        initiated_block=_int_field(raw.get('initiatedBlock')),
        timeout_block=_int_field(raw.get('timeoutBlock')),
        fulfilled_block=_int_field(raw.get('fulfilledBlock')),
        completed_block=_int_field(raw.get('completedBlock')),
    )


def fetch_swap_from_das(swap_id: int, timeout: float = 15.0) -> Optional[Swap]:
    """GET `/swaps/{swapId}`; returns None if missing or on transport/parse errors."""
    url = f'{get_das_base_url()}/swaps/{swap_id}'
    try:
        r = requests.get(url, headers=_DAS_HEADERS, timeout=timeout)
        r.raise_for_status()
    except requests.RequestException:
        return None
    try:
        payload = r.json()
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    raw = payload.get('swap')
    if not isinstance(raw, dict):
        return None
    try:
        sw = swap_from_das(raw, fallback_swap_id=swap_id)
    except (TypeError, ValueError):
        return None
    if sw.source_chain not in SUPPORTED_CHAINS or sw.dest_chain not in SUPPORTED_CHAINS:
        return None
    return sw

"""Tests for Allways DAS (indexer) swap parsing."""

from allways.classes import SwapStatus
from allways.cli.das_api import swap_from_das


def test_swap_from_das_maps_api_payload():
    raw = {
        'swapId': '2',
        'status': 'COMPLETED',
        'userAddress': '5HL1sRC4je8MYaSQ4nd9imBqzZTSEbntgwNx9ngGnHQjURqQ',
        'minerHotkey': '5E7wEgYdY38yq26BMyV2tU54qEpiHgUMA2FxBpdzwY2R7n23',
        'taoAmount': '0.149100000000000000',
        'sourceChain': 'btc',
        'destChain': 'tao',
        'sourceAmount': '30000',
        'destAmount': '149100000',
        'rate': '497.000000000000000000',
        'userSourceAddress': 'bc1qtest',
        'userDestAddress': '5HL1sRC4je8MYaSQ4nd9imBqzZTSEbntgwNx9ngGnHQjURqQ',
        'minerSourceAddress': 'bc1qminer',
        'sourceTxHash': 'aa' * 32,
        'destTxHash': '0xbb' + 'cc' * 31,
        'timeoutBlock': '6759001',
        'initiatedBlock': '6758971',
        'fulfilledBlock': '6758973',
        'completedBlock': '6758979',
    }
    s = swap_from_das(raw, fallback_swap_id=99)
    assert s.id == 2
    assert s.status == SwapStatus.COMPLETED
    assert s.source_chain == 'btc'
    assert s.dest_chain == 'tao'
    assert s.tao_amount == 149_100_000
    assert s.source_amount == 30_000
    assert s.dest_amount == 149_100_000
    assert s.initiated_block == 6_758_971
    assert s.completed_block == 6_758_979


def test_swap_from_das_fallback_id_when_swap_id_absent():
    raw = {
        'status': 'COMPLETED',
        'userAddress': '5HL1sRC4je8MYaSQ4nd9imBqzZTSEbntgwNx9ngGnHQjURqQ',
        'minerHotkey': '5E7wEgYdY38yq26BMyV2tU54qEpiHgUMA2FxBpdzwY2R7n23',
        'taoAmount': '0.149100000000000000',
        'sourceChain': 'btc',
        'destChain': 'tao',
        'sourceAmount': '30000',
        'destAmount': '149100000',
        'rate': '497.000000000000000000',
        'userSourceAddress': 'bc1qtest',
        'userDestAddress': '5HL1sRC4je8MYaSQ4nd9imBqzZTSEbntgwNx9ngGnHQjURqQ',
    }
    s = swap_from_das(raw, fallback_swap_id=42)
    assert s.id == 42

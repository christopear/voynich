"""Compatibility scheduling for the original September pilot search semantics."""
from voynich.decipher_search.core import search_restart


def legacy_recovery_runs(ciphertext, training, config):
    return [search_restart(ciphertext, training, config, restart)
            for restart in range(config.restarts)]

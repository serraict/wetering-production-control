"""Regression guard: importing opcua.leuze installs the LenientCertificate
monkey-patch on asyncua.crypto.uacrypto.

The patch is load-bearing for connecting to the real Leuze DCR 202iC
(firmware V2.4.0), which serves a malformed Application Instance
certificate that strict cryptography parsers reject. The behave suite
runs against the test server with VINEAPP_OPCUA_SECURITY=none, so it
never exercises this path — without this test, removing the
module-level patch in leuze.py would silently break the prod
connection at next deploy.
"""

from __future__ import annotations

import importlib

from asyncua.crypto import uacrypto


def test_importing_leuze_installs_lenient_uacrypto_patches():
    # Reload rather than rely on first-import caching from a prior test:
    # if someone deletes the patch from leuze.py's module body, the
    # reload re-runs the body and the assertion below catches it.
    leuze = importlib.import_module("production_control.opcua.leuze")
    leuze = importlib.reload(leuze)

    assert uacrypto.x509_from_der is leuze._lenient_x509_from_der
    assert uacrypto.der_from_x509 is leuze._patched_der_from_x509
    assert uacrypto.load_certificate is leuze._lenient_load_certificate

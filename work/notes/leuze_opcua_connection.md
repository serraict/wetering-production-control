# Leuze DCR 202iC OPC/UA Connection (Ontsapelaar)

## Device
- **Model**: Leuze DCR 202iC FIX-M1-102-R3 (barcode/QR scanner)
- **IP**: 192.168.50.41, port 4840
- **Firmware**: 1.5.2 (build 321, 2024-04-08)
- **Serial**: 70019323066
- **Server Application URI**: urn:LeuzeElectronic:DCR2xx:DCR2xx-4450AC

## How to connect (working)

Requires monkey-patching asyncua due to malformed server certificate.
Use `scripts/browse_leuze.py` as reference — it patches `uacrypto.x509_from_der`,
`uacrypto.load_certificate`, and `uacrypto.der_from_x509` to handle the Leuze's
malformed PrintableString ASN.1 field using pyasn1 as a lenient parser.

```python
import asyncio

# IMPORTANT: apply monkey-patches BEFORE connecting.
# Copy the patching code from scripts/browse_leuze.py (lines 1-127)
# or import it as a module.

from asyncua import Client

async def read_leuze():
    client = Client("opc.tcp://192.168.50.41:4840")
    client.set_user("Martin")  # Capital M!
    client.set_password("12345678")
    await client.set_security_string(
        "Basic256Sha256,SignAndEncrypt,"
        "certs/client_cert.der,"
        "certs/client_cert_key.pem"
    )
    async with client:
        # Read last scan
        node = client.get_node("ns=5;i=6122")
        value = await node.read_value()
        print(f"LastScanData = {value}")

        # Read scan status
        node = client.get_node("ns=5;i=6199")
        active = await node.read_value()
        print(f"ScanActive = {active}")

asyncio.run(read_leuze())
```

### Required files
- `certs/client_cert.der` — our client certificate
- `certs/client_cert_key.pem` — our client private key
- `pyasn1` package (dependency, needed for lenient cert parsing)

### Credentials
- Username: `Martin` (capital M, case-sensitive!)
- Password: `12345678`

### Why standard uabrowse doesn't work
The Leuze scanner's server certificate has a non-standard character in a
PrintableString ASN.1 field. Python's `cryptography` library rejects it with:
```
ValueError: error parsing asn1 value: ParseError { kind: InvalidValue,
  location: [3, 0, "AttributeTypeValue::value", "AttributeValue::PrintableString"] }
```
The `LenientCertificate` class in `scripts/browse_leuze.py` works around this
by extracting the public key via pyasn1 without fully parsing the certificate.

## Key OPC/UA nodes

### Scan data (namespace `http://leuze.com/OpcUa/DCR200/`, ns=5)
Browse path: `Objects > DeviceSet > DCR200 > AutoID > LastScanData`

| Node | NodeId | Type | Description |
|------|--------|------|-------------|
| LastScanData | ns=5;i=6122 | String | Last scanned barcode/QR value |
| ScanActive | ns=5;i=6199 | Boolean | Whether scanning is active |
| ScanStart | ns=5;i=7003 | Method | Start scanning |
| ScanStop | ns=5;i=7004 | Method | Stop scanning |

### Device info (ns=5)
| Node | NodeId | Type | Description |
|------|--------|------|-------------|
| DeviceTemperature | ns=5;i=6116 | Float | Device temperature |
| SerialNumber | ns=5;i=6029 | String | 70019323066 |
| Model | ns=5;i=6024 | LocalizedText | DCR 202iC FIX-M1-102-R3 |
| SoftwareRevision | ns=5;i=6030 | String | V 2.4.0 |

## Certificate generation
```bash
uv run python scripts/generate_opcua_certificate.py --output-dir certs --hostname 192.168.50.140
```
The client cert (`client_cert.der`) must be added to the Leuze scanner's
trusted certificates (via its web interface or Leuze configuration tool).

## Browse command
```bash
uv run python scripts/browse_leuze.py --user Martin --password 12345678 --depth 5
```

## Namespaces
| Index | URI |
|-------|-----|
| 0 | http://opcfoundation.org/UA/ |
| 1 | urn:LeuzeElectronic:DCR2xx:DCR2xx-4450AC |
| 2 | http://opcfoundation.org/UA/DI/ |
| 3 | http://opcfoundation.org/UA/AutoID/ |
| 4 | http://leuze.com/OpcUa/ |
| 5 | http://leuze.com/OpcUa/DCR200/ |

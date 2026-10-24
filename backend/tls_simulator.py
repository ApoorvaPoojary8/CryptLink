
import os
import hashlib
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import (
    x25519,
    rsa,
    padding,
)
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class TLSHandshakeSimulator:
    def __init__(self):
        self.events = []
        self.status = "NOT_STARTED"

    def add_event(self, name, details):
        self.events.append({
            "step": len(self.events) + 1,
            "name": name,
            "details": details,
        })

    def get_result(self):
        return {
            "status": self.status,
            "total_steps": len(self.events),
            "events": self.events,
        }

    def run(self, simulate_failure=None):
        self.events = []
        self.status = "IN_PROGRESS"

        try:
            # Step 1: ClientHello
            client_random = os.urandom(32)

            self.add_event("ClientHello", {
                "protocol_version": "TLS 1.3 (simulated)",
                "client_random": client_random.hex(),
                "supported_key_exchange": "X25519",
                "supported_cipher_suite": "AES-256-GCM (illustrative)",
            })

            # Step 2: ServerHello and ephemeral X25519 keys
            client_private = x25519.X25519PrivateKey.generate()
            server_private = x25519.X25519PrivateKey.generate()

            client_public = client_private.public_key()
            server_public = server_private.public_key()

            server_random = os.urandom(32)

            server_public_bytes = server_public.public_bytes(
                serialization.Encoding.Raw,
                serialization.PublicFormat.Raw,
            )

            self.add_event("ServerHello", {
                "protocol_version": "TLS 1.3 (simulated)",
                "server_random": server_random.hex(),
                "selected_key_exchange": "X25519",
                "server_public_key": server_public_bytes.hex(),
            })

            # Step 3: Generate a temporary self-signed RSA certificate
            certificate_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )

            subject = x509.Name([
                x509.NameAttribute(
                    NameOID.COMMON_NAME,
                    "localhost",
                )
            ])

            now = datetime.now(timezone.utc)

            certificate = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(subject)
                .public_key(certificate_key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now - timedelta(minutes=1))
                .not_valid_after(now + timedelta(days=7))
                .add_extension(
                    x509.BasicConstraints(
                        ca=False,
                        path_length=None,
                    ),
                    critical=True,
                )
                .sign(certificate_key, hashes.SHA256())
            )

            # Verify the self-signed certificate signature.
            certificate.public_key().verify(
                certificate.signature,
                certificate.tbs_certificate_bytes,
                padding.PKCS1v15(),
                certificate.signature_hash_algorithm,
            )

            certificate_pem = certificate.public_bytes(
                serialization.Encoding.PEM
            ).decode("utf-8")

            self.add_event("ServerCertificate", {
                "subject": certificate.subject.rfc4514_string(),
                "issuer": certificate.issuer.rfc4514_string(),
                "self_signature_valid": True,
                "trusted": False,
                "trust_note": (
                    "Self-signed certificate; the client's "
                    "trust in the server identity is not established."
                ),
                "certificate_pem": certificate_pem,
            })

            # Step 4: CertificateVerify
            # Sign handshake data using the certificate private key.
            transcript = (
                client_random
                + server_random
                + server_public_bytes
            )

            signature = certificate_key.sign(
                transcript,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )

            # Optional negative test: tamper with the signature.
            if simulate_failure == "tampered_signature":
                signature = (
                    bytes([signature[0] ^ 1])
                    + signature[1:]
                )

            try:
                certificate.public_key().verify(
                    signature,
                    transcript,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH,
                    ),
                    hashes.SHA256(),
                )

            except InvalidSignature:
                self.add_event("CertificateVerify", {
                    "algorithm": "RSA-PSS with SHA-256",
                    "signature_valid": False,
                    "status": "FAILED",
                })

                self.status = "FAILED"

                self.add_event("HandshakeFailed", {
                    "reason": (
                        "CertificateVerify signature validation failed"
                    ),
                    "security_event": "Signature tampering detected",
                })

                return self.get_result()

            self.add_event("CertificateVerify", {
                "algorithm": "RSA-PSS with SHA-256",
                "signature_valid": True,
                "status": "SUCCESS",
            })

            # Step 5: X25519 shared-secret derivation
            client_secret = client_private.exchange(server_public)
            server_secret = server_private.exchange(client_public)

            if client_secret != server_secret:
                raise ValueError("Shared secrets do not match")

            self.add_event("KeyExchange", {
                "algorithm": "X25519",
                "shared_secrets_match": True,
                "client_fingerprint": hashlib.sha256(
                    client_secret
                ).hexdigest()[:16],
                "server_fingerprint": hashlib.sha256(
                    server_secret
                ).hexdigest()[:16],
            })

            # Step 6: Derive session keys using HKDF-SHA256
            def derive_key(secret):
                return HKDF(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=None,
                    info=b"CryptLink session key",
                ).derive(secret)

            client_key = derive_key(client_secret)
            server_key = derive_key(server_secret)

            if client_key != server_key:
                raise ValueError("Session keys do not match")

            self.add_event("HandshakeComplete", {
                "session_keys_match": True,
                "session_key_bits": 256,
                "session_key_fingerprint": hashlib.sha256(
                    client_key
                ).hexdigest()[:16],
                "status": "SUCCESS",
            })

            self.status = "SUCCESS"
            return self.get_result()

        except Exception:
            self.status = "FAILED"
            raise

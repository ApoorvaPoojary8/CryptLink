
import os
import hashlib
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh, rsa, padding
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class TLSHandshakeSimulator:
    # Reuse DH parameters across simulator instances.
    # Fresh ephemeral key pairs are generated for every handshake.
    _dh_parameters = None

    def __init__(self):
        self.events = []
        self.status = "NOT_STARTED"

    def add_event(self, name, details):
        self.events.append({
            "step": len(self.events) + 1,
            "name": name,
            "details": details
        })

    def get_result(self):
        return {
            "status": self.status,
            "total_steps": len(self.events),
            "events": self.events
        }

    def run(self):
        self.events = []
        self.status = "IN_PROGRESS"

        try:
            # Step 1: ClientHello
            client_random = os.urandom(32)

            self.add_event("ClientHello", {
                "protocol_version": "TLS 1.3 (simulated)",
                "client_random": client_random.hex(),
                "supported_key_exchange": "Diffie-Hellman",
                "supported_cipher_suite": "AES-256-GCM (illustrative)"
            })

            # Step 2: ServerHello and ephemeral DH keys
            # Generate DH parameters only once per process.
            if TLSHandshakeSimulator._dh_parameters is None:
                TLSHandshakeSimulator._dh_parameters = (
                    dh.generate_parameters(
                        generator=2,
                        key_size=2048
                    )
                )

            parameters = TLSHandshakeSimulator._dh_parameters

            # Generate fresh ephemeral key pairs for this handshake.
            client_private = parameters.generate_private_key()
            server_private = parameters.generate_private_key()

            client_public = client_private.public_key()
            server_public = server_private.public_key()

            server_random = os.urandom(32)

            self.add_event("ServerHello", {
                "protocol_version": "TLS 1.3 (simulated)",
                "server_random": server_random.hex(),
                "selected_key_exchange": "Diffie-Hellman",
                "server_public_key": str(
                    server_public.public_numbers().y
                )
            })

            # Step 3: Generate a self-signed server certificate
            certificate_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )

            subject = x509.Name([
                x509.NameAttribute(
                    NameOID.COMMON_NAME,
                    "localhost"
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
                        path_length=None
                    ),
                    critical=True
                )
                .sign(
                    certificate_key,
                    hashes.SHA256()
                )
            )

            # Verify the certificate's self-signature.
            certificate.public_key().verify(
                certificate.signature,
                certificate.tbs_certificate_bytes,
                padding.PKCS1v15(),
                certificate.signature_hash_algorithm
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
                    "Self-signed certificate; "
                    "identity is not automatically trusted."
                ),
                "certificate_pem": certificate_pem
            })

            # Step 4: Diffie-Hellman shared secret
            client_secret = client_private.exchange(server_public)
            server_secret = server_private.exchange(client_public)

            if client_secret != server_secret:
                raise ValueError("Shared secrets do not match")

            self.add_event("KeyExchange", {
                "algorithm": "Diffie-Hellman",
                "shared_secrets_match": True,
                "client_fingerprint": hashlib.sha256(
                    client_secret
                ).hexdigest()[:16],
                "server_fingerprint": hashlib.sha256(
                    server_secret
                ).hexdigest()[:16]
            })

            # Step 5: Derive session keys using HKDF-SHA256
            def derive_key(secret):
                return HKDF(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=None,
                    info=b"CryptLink session key"
                ).derive(secret)

            client_key = derive_key(client_secret)
            server_key = derive_key(server_secret)

            if client_key != server_key:
                raise ValueError("Session keys do not match")

            session_key_fingerprint = hashlib.sha256(
                client_key
            ).hexdigest()[:16]

            self.add_event("HandshakeComplete", {
                "session_keys_match": True,
                "session_key_bits": 256,
                "session_key_fingerprint": session_key_fingerprint,
                "status": "SUCCESS"
            })

            self.status = "SUCCESS"
            return self.get_result()

        except Exception:
            self.status = "FAILED"
            raise

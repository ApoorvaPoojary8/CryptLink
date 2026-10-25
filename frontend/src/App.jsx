import { useState } from "react";
import {
  ShieldCheck,
  LockKeyhole,
  Server,
  Monitor,
  Play,
  RotateCcw,
  CheckCircle2,
  Circle,
  LoaderCircle,
  AlertCircle,
  KeyRound,
  FileBadge,
  Activity,
  ShieldAlert,
} from "lucide-react";
import "./App.css";

const API = "http://127.0.0.1:5000/api";

const handshakeSteps = [
  {
    name: "ClientHello",
    description: "Client proposes protocol parameters",
    icon: Monitor,
  },
  {
    name: "ServerHello",
    description: "Server selects connection parameters",
    icon: Server,
  },
  {
    name: "ServerCertificate",
    description: "Server presents its certificate",
    icon: FileBadge,
  },
  {
    name: "CertificateVerify",
    description: "Server proves possession of its certificate private key",
    icon: ShieldCheck,
  },
  {
    name: "KeyExchange",
    description: "Client and server derive a shared secret",
    icon: KeyRound,
  },
  {
    name: "HandshakeComplete",
    description: "Session keys are successfully derived",
    icon: ShieldCheck,
  },
  {
    name: "HandshakeFailed",
    description: "The handshake stopped after a security check failed",
    icon: ShieldAlert,
  },
];

function App() {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState("NOT_STARTED");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedStep, setSelectedStep] = useState(null);

  const runHandshake = async (simulateAttack = false) => {
    setLoading(true);
    setError("");
    setEvents([]);
    setSelectedStep(null);
    setStatus("IN_PROGRESS");

    try {
      const response = await fetch(`${API}/handshake/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        ...(simulateAttack
          ? {
              body: JSON.stringify({
                simulate_failure: "tampered_signature",
              }),
            }
          : {}),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Handshake request failed");
      }

      const receivedEvents = data.events || [];

      // Reveal handshake events one at a time instead of showing them all at once.
      const animationDelay = 750;
      for (let index = 0; index < receivedEvents.length; index += 1) {
        setEvents((currentEvents) => [
          ...currentEvents,
          receivedEvents[index],
        ]);
        setSelectedStep(index);
        await new Promise((resolve) => setTimeout(resolve, animationDelay));
      }

      setStatus(data.status || "FAILED");
    } catch (err) {
      setStatus("FAILED");
      setError(
        `${err.message}. Check that the Flask backend is running on port 5000.`
      );
    } finally {
      setLoading(false);
    }
  };

  const startHandshake = () => runHandshake(false);
  const simulateAttack = () => runHandshake(true);

  const resetHandshake = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API}/handshake/reset`, {
        method: "POST",
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.message || "Could not reset handshake");
      }

      setEvents([]);
      setStatus("NOT_STARTED");
      setSelectedStep(null);
    } catch (err) {
      setError(
        `${err.message}. Check that the Flask backend is running on port 5000.`
      );
    } finally {
      setLoading(false);
    }
  };

  const activeEvent =
    selectedStep !== null ? events[selectedStep] : null;

  const formatName = (value) =>
    value.replace(/([a-z])([A-Z])/g, "$1 $2");

  const statusLabel = {
    NOT_STARTED: "Ready to begin",
    IN_PROGRESS: "Handshake in progress",
    SUCCESS: "Secure session simulated",
    FAILED: "Handshake failed",
  }[status] || status;

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#home">
          <div className="brand-icon">
            <ShieldCheck size={24} />
          </div>
          <div>
            <h1>CryptLink</h1>
            <span>SECURE CONNECTION LAB</span>
          </div>
        </a>

        <div className="topbar-right">
          <span className="live-dot" />
          <span>LOCAL SIMULATOR</span>
          <div className="version-badge">TLS 1.3 DEMO</div>
        </div>
      </header>

      <main className="main-content" id="home">
        <section className="hero">
          <div className="eyebrow">
            <LockKeyhole size={14} />
            NETWORK SECURITY / HANDSHAKE LAB
          </div>

          <h2>
            Understand the handshake.
            <br />
            <span>Visualize the trust.</span>
          </h2>

          <p>
            Explore how a client and server negotiate parameters,
            exchange cryptographic information, and derive matching
            session keys.
          </p>
        </section>

        <section className="status-grid">
          <div className="metric-card">
            <div className="metric-top">
              <span>PROTOCOL</span>
              <Activity size={17} />
            </div>
            <strong>TLS 1.3</strong>
            <small>Handshake simulation</small>
          </div>

          <div className="metric-card">
            <div className="metric-top">
              <span>KEY EXCHANGE</span>
              <KeyRound size={17} />
            </div>
            <strong>X25519</strong>
            <small>Ephemeral key pairs</small>
          </div>

          <div className="metric-card">
            <div className="metric-top">
              <span>SESSION KEY</span>
              <LockKeyhole size={17} />
            </div>
            <strong>256-bit</strong>
            <small>HKDF-SHA256 derived</small>
          </div>

          <div className="metric-card">
            <div className="metric-top">
              <span>CONNECTION</span>
              <ShieldCheck size={17} />
            </div>
            <strong className={`status-text ${status.toLowerCase()}`}>
              {status === "SUCCESS"
                ? "Verified"
                : status === "FAILED"
                  ? "Failed"
                  : "Standby"}
            </strong>
            <small>{statusLabel}</small>
          </div>
        </section>

        <section className="workspace">
          <div className="panel flow-panel">
            <div className="panel-heading">
              <div>
                <span className="section-label">01 / MESSAGE FLOW</span>
                <h3>Handshake sequence</h3>
              </div>
              <span className="step-counter">
                {events.length} events
              </span>
            </div>

            <div className="participants">
              <div className="participant">
                <div className="participant-icon client-icon">
                  <Monitor size={22} />
                </div>
                <div>
                  <strong>Client</strong>
                  <small>Browser simulation</small>
                </div>
              </div>

              <div className="participant-line">
                <span>EXCHANGE</span>
              </div>

              <div className="participant">
                <div className="participant-icon server-icon">
                  <Server size={22} />
                </div>
                <div>
                  <strong>Server</strong>
                  <small>Local Flask engine</small>
                </div>
              </div>
            </div>

            <div className="timeline">
              {handshakeSteps.map((step, index) => {
                const eventIndex = events.findIndex(
                  (item) => item.name === step.name
                );
                const event = eventIndex >= 0 ? events[eventIndex] : null;
                const Icon = step.icon;
                const isActive = selectedStep === eventIndex;

                return (
                  <div className="timeline-item" key={step.name}>
                    <div className="timeline-marker">
                      <span
                        className={`step-number ${
                          event ? "completed" : ""
                        } ${isActive ? "selected" : ""}`}
                      >
                        {event ? <CheckCircle2 size={19} /> : index + 1}
                      </span>
                      {index < handshakeSteps.length - 1 && (
                        <span
                          className={`timeline-connector ${
                            event ? "completed" : ""
                          }`}
                        />
                      )}
                    </div>

                    <button
                      type="button"
                      className={`timeline-content ${
                        isActive ? "selected" : ""
                      } ${event ? "available" : ""}`}
                      disabled={!event || loading}
                      onClick={() => setSelectedStep(eventIndex)}
                    >
                      <div className="timeline-icon">
                        <Icon size={19} />
                      </div>
                      <div className="timeline-copy">
                        <strong>{step.name}</strong>
                        <small>{step.description}</small>
                      </div>
                      <span className="event-state">
                        {event ? "RECEIVED" : "PENDING"}
                      </span>
                    </button>
                  </div>
                );
              })}
            </div>

            <div className="action-row">
              <button
                type="button"
                className="primary-button"
                onClick={startHandshake}
                disabled={loading}
              >
                {loading ? (
                  <LoaderCircle className="spin" size={18} />
                ) : (
                  <Play size={18} />
                )}
                {loading ? "Running..." : "Start handshake"}
              </button>

              <button
                type="button"
                className="secondary-button"
                onClick={simulateAttack}
                disabled={loading}
              >
                <ShieldAlert size={17} />
                Simulate signature attack
              </button>

              <button
                type="button"
                className="secondary-button"
                onClick={resetHandshake}
                disabled={loading}
              >
                <RotateCcw size={17} />
                Reset
              </button>
            </div>

            {error && (
              <div className="error-banner" role="alert">
                <AlertCircle size={18} />
                {error}
              </div>
            )}
          </div>

          <div className="panel details-panel">
            <div className="panel-heading">
              <div>
                <span className="section-label">02 / EVENT INSPECTOR</span>
                <h3>Message details</h3>
              </div>
              <FileBadge size={22} className="muted-icon" />
            </div>

            {activeEvent ? (
              <div className="event-details">
                <div className="event-title">
                  <span className="detail-tag">
                    STEP {activeEvent.step}
                  </span>
                  <h4>{formatName(activeEvent.name)}</h4>
                </div>

                <p className="detail-description">
                  {handshakeSteps.find(
                    (step) => step.name === activeEvent.name
                  )?.description || "Handshake event details"}
                </p>

                <div className="data-heading">
                  <span>EVENT PAYLOAD</span>
                  <span>JSON</span>
                </div>

                <pre className="json-view">
                  {JSON.stringify(activeEvent.details, null, 2)}
                </pre>

                {activeEvent.name === "ServerCertificate" && (
                  <div className="certificate-warning">
                    <AlertCircle size={17} />
                    Self-signature validity does not establish certificate
                    trust or authenticate the key exchange.
                  </div>
                )}

                {activeEvent.name === "CertificateVerify" &&
                  activeEvent.details?.signature_valid === false && (
                    <div className="error-banner" role="alert">
                      <ShieldAlert size={18} />
                      Signature verification failed. The handshake was stopped.
                    </div>
                  )}

                {activeEvent.name === "HandshakeFailed" && (
                  <div className="error-banner" role="alert">
                    <ShieldAlert size={18} />
                    The handshake failed because a security check did not pass.
                  </div>
                )}

                {activeEvent.name === "HandshakeComplete" && (
                  <div className="success-banner">
                    <CheckCircle2 size={19} />
                    Both sides derived matching session keys.
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">
                  <Circle size={30} />
                </div>
                <h4>Awaiting handshake data</h4>
                <p>
                  Start the handshake to inspect message payloads,
                  certificate information, and key-exchange results.
                </p>
              </div>
            )}
          </div>
        </section>

        <section className="bottom-note">
          <ShieldCheck size={19} />
          <div>
            <strong>Handshake security overview</strong>
            <p>
              CryptLink demonstrates handshake concepts locally. It
              does not implement the complete TLS record protocol or
              a fully authenticated TLS connection.
            </p>
          </div>
        </section>

        <footer>
          <span>CRYPTLINK © 2026</span>
          <span>SECURE COMMUNICATION WEB APPLICATION</span>
        </footer>
      </main>
    </div>
  );
}

export default App;

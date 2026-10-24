from tls_simulator import TLSHandshakeSimulator

simulator = TLSHandshakeSimulator()
result = simulator.run()

print("Status:", result["status"])

for event in result["events"]:
    print(f'{event["step"]}. {event["name"]}')

print("Total steps:", result["total_steps"])
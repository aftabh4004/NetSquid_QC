import netsquid as ns
import pydynaa as pd


class Charlie(pd.Entity):
    ready_event_type = pd.EventType("READY", "Entangled qubit are ready")
    _generate_event_type = pd.EventType("GENERATE", "Generate the entangled qubit pair")
    period = 50
    delay = 10

    def __init__(self):
        self.entangled_qubit = None
        self._generate_handler = pd.EventHandler(self._entangle_qubit) #callback as argumet
        self._wait(self._generate_handler, entity=self, event_type=Charlie._generate_event_type)

    def _entangle_qubit(self, event):
        q1, q2 = ns.qubits.create_qubits(2)
        ns.qubits.operate(q1, ns.H)
        ns.qubits.operate([q1, q2], ns.CX)

        self.entangled_qubit = [q1, q2]
        self._schedule_after(Charlie.delay, Charlie.ready_event_type)
        print(f"{ns.sim_time()}: Charlie has generated Entangled qubit pari")
        self._schedule_after(Charlie.period, Charlie._generate_event_type)

    def start(self):
        print(f"Charlie start generating entangled pair")
        self._schedule_now(Charlie._generate_event_type)


class Alice(pd.Entity):
    ready_event_type = pd.EventType("CORRECTION", "correction is ready")
    _teleport_event_type = pd.EventType("TELEPORT", "Teleport the qubit")
    delay = 20

    def __init__(self, teleport_state):
        self.teleport_state = teleport_state
        self.q0 = None
        self.q1 = None
        self.correction = None
        _teleport_handler = pd.EventHandler(self._handle_teleport)
        self._wait(_teleport_handler, entity=self, event_type=Alice._teleport_event_type)

    def wait_for_charlie(self, charlie):
        self._qubit_handler = pd.EventHandler(self._handle_qubit)
        self._wait(self._qubit_handler, entity=charlie, event_type=charlie.ready_event_type)

    def _handle_qubit(self, event):
        self.q0, = ns.qubits.create_qubits(1, no_state=True)
        self.q1 = event.source.entangled_qubit[0]
        ns.qubits.assign_qstate([self.q0], self.teleport_state)
        self._schedule_after(Alice.delay, self._teleport_event_type)
        print(f"{ns.sim_time()}: Alice received entangle qubit")

    def _handle_teleport(self, event):
        ns.qubits.operate([self.q0, self.q1], ns.CX)
        ns.qubits.operate(self.q0, ns.H)

        m1, __ = ns.qubits.measure(self.q0)
        m2, __ = ns.qubits.measure(self.q1)

        self.correction = [m1, m2]
        self._schedule_now(Alice.ready_event_type)
        print(f"{ns.sim_time()}: Alice measure the correction and sending ")


class Bob(pd.Entity):

    def wait_for_teleport(self, alice, charlie):
        charlie_ready_event_exp = pd.EventExpression(source=charlie, event_type=Charlie.ready_event_type)
        alice_ready_event_exp = pd.EventExpression(source=alice, event_type=Alice.ready_event_type)

        both_ready_event_exp = charlie_ready_event_exp & alice_ready_event_exp
        self._teleport_handler = pd.ExpressionHandler(self._handle_teleport)
        self._wait(self._teleport_handler, expression=both_ready_event_exp)

    def _handle_teleport(self, event_exp):
        qubit = event_exp.first_term.atomic_source.entangled_qubit[1]
        alice = event_exp.second_term.atomic_source
        self._apply_correction(qubit, alice)

    def _apply_correction(self, qubit, alice):
        m0, m1 = alice.correction
        if m1 == 1:
            ns.qubits.operate(qubit, ns.X)
        if m0 == 1:
            ns.qubits.operate(qubit, ns.Z)

        fidelity = ns.qubits.fidelity(qubit, alice.teleport_state, squared=True)
        print(f"{ns.sim_time():.1f}: Bob received entangled qubit and corrections!"
              f" Fidelity = {fidelity:.3f}")


class NoisyBob(Bob):
    depolar_rate = 1e7

    def _handle_teleport(self, event_exp):
        charlie_exp = event_exp.first_term
        alice_exp = event_exp.second_term
        delay = ns.sim_time() - charlie_exp.triggered_time
        qubit = charlie_exp.atomic_source.entangled_qubit[1]
        ns.qubits.delay_depolarize(qubit, NoisyBob.depolar_rate, delay)

        self._apply_correction(qubit, alice_exp.atomic_source)


def setup_network(a, b, c):
    a.wait_for_charlie(c)
    b.wait_for_teleport(a, c)
    c.start()


alice = Alice(teleport_state=ns.h1)
bob = Bob()
noisybob = NoisyBob()
charlie = Charlie()
setup_network(alice, noisybob, charlie)

ns.set_qstate_formalism(ns.QFormalism.DM)
ns.sim_run(end_time=50)
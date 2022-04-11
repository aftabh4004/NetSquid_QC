import netsquid as ns
from netsquid.components import QuantumChannel, ClassicalChannel, QuantumMemory
from netsquid.components.qsource import QSource, SourceStatus
from netsquid.nodes.connections import Connection
from netsquid.components.models import  FibreDelayModel, DepolarNoiseModel, FixedDelayModel
from netsquid.nodes import Node
import netsquid.qubits.ketstates as ks
from netsquid.qubits import StateSampler


class ClassicalConnection(Connection):
    def __init__(self, length):
        super().__init__(name="ClassicalChannel")
        self.length = length
        cchannel = ClassicalChannel("Alice2Bob", length=self.length, models={'delay_model': FibreDelayModel()})
        self.add_subcomponent(cchannel, forward_input=[("A", "send")], forward_output=[("B", "recv")])


class EntanglingChannel(Connection):
    def __init__(self, length, source_freq):
        super().__init__("EntanglingQubit")
        timing_model = FixedDelayModel(delay=(1e9/source_freq))
        qsource = QSource("Charlie", state_sampler=StateSampler([ks.b00], [1.0]),timing_model=timing_model,
                          status=SourceStatus.INTERNAL,num_ports=2)
        self.add_subcomponent(qsource)

        q_channel_c2a = QuantumChannel("QC_Charlie2Alice", models={'delay_model': FibreDelayModel()}, length=length/2)
        q_channel_c2b = QuantumChannel("QC_Charlie2Bob", models={'delay_model': FibreDelayModel()}, length=length/2)

        self.add_subcomponent(q_channel_c2b, forward_output=[("B", "recv")])
        self.add_subcomponent(q_channel_c2a, forward_output=[("A", "recv")])

        qsource.ports['qout0'].connect(q_channel_c2a.ports["send"])
        qsource.ports['qout1'].connect(q_channel_c2b.ports["send"])


def network_setup(node_distance=4e-3, depolar_rate=1e7):
    noise_model = DepolarNoiseModel(depolar_rate=depolar_rate)
    alice_qmem = QuantumMemory("AliceMemory", num_positions=2, memory_noise_models=[noise_model]*2)
    alice = Node("Alice", qmemory=alice_qmem, port_names=["cout_bob", "qin_charlie"])

    bob_qmem = QuantumMemory("BobMemory", num_positions=1, memory_noise_models=[noise_model])
    bob = Node("Bob", qmemory=bob_qmem, port_names=["cin_alice", "qin_charlie"])

    alice.ports['qin_charlie'].forward_input(alice.qmemory.ports['qin1'])
    bob.ports['qin_charlie'].forward_input(bob.qmemory.ports['qin0'])

    c_conn = ClassicalConnection(node_distance)
    entagling_conn = EntanglingChannel(node_distance, source_freq=2e7)

    alice.ports["cout_bob"].connect(c_conn.ports["A"])
    bob.ports["cin_alice"].connect(c_conn.ports["B"])

    alice.ports['qin_charlie'].connect(entagling_conn.ports["A"])
    bob.ports["qin_charlie"].connect(entagling_conn.ports["B"])

    return alice, bob, entagling_conn, c_conn


ns.set_qstate_formalism(ns.QFormalism.DM)
alice, bob, *_ = network_setup()
stats = ns.sim_run(91)
qA, = alice.qmemory.peek(positions=[1])
qB, = bob.qmemory.peek(positions=[0])
qA, qB
fidelity = ns.qubits.fidelity([qA, qB], ns.b00)
print(f"Entangled fidelity (after 5 ns wait) = {fidelity:.3f}")







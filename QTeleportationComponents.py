import netsquid as ns
import pydynaa
from netsquid.qubits.state_sampler import StateSampler
import netsquid.qubits.ketstates as ks
from netsquid.components import QuantumMemory, Port
from netsquid.components.cchannel import ClassicalChannel
from netsquid.components.qchannel import QuantumChannel
from netsquid.components.models.delaymodels import FibreDelayModel, FixedDelayModel
from netsquid.components.models.qerrormodels import DepolarNoiseModel
from netsquid.components.qsource import QSource, SourceStatus
ns.set_qstate_formalism(ns.QFormalism.DM)
class Alice(pydynaa.Entity):
    def __init__(self, teleport_state, cchannel_send_port):
        self.teleport_state = teleport_state
        self.qmemory = QuantumMemory(name="AliceQmem", num_positions=2)
        self.cchannel_send_port = cchannel_send_port

        self._wait(pydynaa.EventHandler(self._handle_input_qubit), entity=self.qmemory.ports['qin1'], event_type=Port.evtype_input)
        self.qmemory.ports['qin1'].notify_all_input = True

    def _handle_input_qubit(self, event):
        qubit = ns.qubits.create_qubits(1, no_state=True)
        ns.qubits.assign_qstate(qubit, self.teleport_state)

        self.qmemory.put(qubit, positions=[0])
        self.qmemory.operate(ns.CX, positions=[0, 1])
        self.qmemory.operate(ns.H, positions=[0])

        [m0, m1], prob = self.qmemory.measure(positions=[0, 1], observable=ns.Z, discard=True)

        self.cchannel_send_port.tx_input([m0, m1])

        print(f"{ns.sim_time():.1f}: Alice received entangled qubit, "
              f"measured qubits & sending corrections")


class Bob(pydynaa.Entity):
    depolar_rate = 1e7  # depolarization rate of waiting qubits [Hz]

    def __init__(self, cchannel_recv_port):
        self.cchannel_recv_port = cchannel_recv_port
        noise_model = DepolarNoiseModel(depolar_rate=self.depolar_rate)
        self.qmemory = QuantumMemory(name="BobQmem", num_positions=1, memory_noise_models=[noise_model])

        self.cchannel_recv_port.bind_output_handler(self._handle_correction)

    def _handle_correction(self, message):
        [m0, m1] = message.items

        if m0:
            self.qmemory.operate(ns.X, positions=[0])
        if m1:
            self.qmemory.operate(ns.Z, positions=[0])

        qubit = self.qmemory.pop(positions=[0])
        fidelity = ns.qubits.fidelity(qubit, ns.y0, squared=True)
        print(f"{ns.sim_time():.1f}: Bob received entangled qubit and corrections!"
              f" Fidelity = {fidelity:.3f}")


def setup_network(alice, bob, charlie, length = 4e-3):
    qchannel_c2a = QuantumChannel(name="Charlie->Alice", length=length / 2, models={'delay_model': FibreDelayModel()})
    qchannel_c2b = QuantumChannel(name="Charlie->Bob", length=length / 2, models={'delay_model': FibreDelayModel()})

    qchannel_c2a.ports['recv'].connect(alice.qmemory.ports['qin1'])
    qchannel_c2b.ports['recv'].connect(bob.qmemory.ports['qin0'])

    qchannel_c2a.ports['send'].connect(charlie.ports['qout0'])
    qchannel_c2b.ports['send'].connect(charlie.ports['qout1'])


#charlie source
state_sampler = StateSampler([ks.b00], [1.0])

charlie_source = QSource("Charlie", state_sampler, frequency=100, num_ports=2,
                         timing_model=FixedDelayModel(delay=50),
                         status=SourceStatus.INTERNAL)
cchannel = ClassicalChannel(name="CChannel", length=4e-3, models={"delay_model" : FibreDelayModel()})

alice = Alice(teleport_state=ns.y0, cchannel_send_port=cchannel.ports['send'])
bob = Bob(cchannel_recv_port=cchannel.ports['recv'])

setup_network(alice, bob, charlie_source)


stat = ns.sim_run(end_time=100)


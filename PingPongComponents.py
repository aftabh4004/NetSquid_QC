import netsquid as ns
from netsquid.components.qmemory import QuantumMemory
from netsquid.components.models.delaymodels import FibreDelayModel
from netsquid.components import QuantumChannel
from netsquid.components import Port
import pydynaa


class PingEntity(pydynaa.Entity):
    length = 3e-3
    def __init__(self):
        self.qmemory = QuantumMemory(name="pingqmem", num_positions=1)
        self.qchannel = QuantumChannel(name="pingchannel", length=self.length, models={'delay_model': FibreDelayModel()})

        self.qmemory.ports['qout'].connect(self.qchannel.ports['send'])

        self._wait(pydynaa.EventHandler(self._handle_input_qubit),entity=self.qmemory.ports["qin0"], event_type=Port.evtype_input)
        self.qmemory.ports['qin0'].notify_all_input = True

    def wait_for_pong(self, pong_entity):
        self.qmemory.ports['qin0'].connect(pong_entity.qchannel.ports['recv'])

    def _handle_input_qubit(self, event):
        [m], [prob] = self.qmemory.measure(positions=[0], observable=ns.Z)
        label = ["0", "1"]
        print(f"{ns.sim_time()}: Ping Event, Pong Entity measured |{label[m]}> with prob {prob}")
        self.qmemory.pop(positions=[0])

    def start(self, qubit):
        self.qchannel.send(qubit)


class PongEntity(pydynaa.Entity):
    length = 3e-3
    def __init__(self):
        self.qmemory = QuantumMemory(name="pongqmem", num_positions=1)
        self.qchannel = QuantumChannel(name="pongchannel", length=self.length, models={'delay_model': FibreDelayModel()})

        self.qmemory.ports['qout'].connect(self.qchannel.ports['send'])

        self._wait(pydynaa.EventHandler(self._handle_input_qubit), entity=self.qmemory.ports["qin0"],
                   event_type=Port.evtype_input)
        self.qmemory.ports['qin0'].notify_all_input = True

    def wait_for_ping(self, ping_entity):
        self.qmemory.ports['qin0'].connect(ping_entity.qchannel.ports['recv'])

    def _handle_input_qubit(self, event):
        [m], [prob] = self.qmemory.measure(positions=[0], observable=ns.X)
        label = ["+", "-"]
        print(f"{ns.sim_time()}: Ping Event, Pong Entity measured |{label[m]}> with prob {prob}")
        self.qmemory.pop(positions=[0])



ping = PingEntity()
pong = PongEntity()

ping.wait_for_pong(pong)
pong.wait_for_ping(ping)

qubit = ns.qubits.create_qubits(1)
ping.start(qubit)

ns.set_random_state(seed=42)
ns.sim_run(91)
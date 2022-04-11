import netsquid as ns
from netsquid.protocols import NodeProtocol
from netsquid.components import QuantumChannel
from netsquid.nodes import Node, DirectConnection
from netsquid.qubits import qubitapi as qapi


class PingProtocol(NodeProtocol):
    def run(self):
        print(f"Starting Ping protocol at {ns.sim_time()}")
        qubit,  = qapi.create_qubits(1)
        port = self.node.ports["port_to_conn"]
        port.tx_output(qubit)

        while True:
            yield self.await_port_input(port)
            qubit = port.rx_input().items[0]
            m, prob = qapi.measure(qubit, observable=ns.Z)
            labels_z = ["|0>", "|1>"]
            print(f"{ns.sim_time()}: Pong event! {self.node.name} measured "
                  f"{labels_z[m]} with probability {prob:.2f}")
            port.tx_output(qubit)


class PongProtocol(NodeProtocol):
    def run(self):
        print(f"Starting pong protocol at {ns.sim_time()}")
        port = self.node.ports["port_to_conn"]
        while True:
            yield self.await_port_input(port)
            qubit = port.rx_input().items[0]
            m, prob = qapi.measure(qubit, observable=ns.X)
            labels_x = ["|+>", "|->"]
            print(f"{ns.sim_time()}: Ping event! {self.node.name} measured "
                  f"{labels_x[m]} with probability {prob:.2f}")
            port.tx_output(qubit)


ping_node = Node("ping_node", port_names=["port_to_conn"])
pong_node = Node("pong_node", port_names=["port_to_conn"])

connection = DirectConnection("direct_connection", channel_AtoB=QuantumChannel("qchannel_lr", delay=10),
                              channel_BtoA=QuantumChannel("qchannel_rl", delay=10))
ping_node.ports["port_to_conn"].connect(connection.ports["A"])
pong_node.ports["port_to_conn"].connect(connection.ports["B"])

ping_protocol = PingProtocol(ping_node)
pong_protocol = PongProtocol(pong_node)

print(ping_protocol.start())
print(pong_protocol.start())

ns.sim_run(91)

pong_protocol.stop()
stat = ns.sim_run()

pong_protocol.start()

ping_protocol.reset()
ns.sim_run(200)

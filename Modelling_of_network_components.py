import netsquid as ns
import netsquid.components.models
from netsquid.components import Channel, QuantumChannel

#No delay
# print("default no delay")
# channel = Channel(name="MyClassicalChannel")
# msg = "Hello World"
# channel.send(msg)
# ns.sim_run()
#
# item, delay = channel.receive()
#
# print(item, delay)


#fixed delay
# delay = 10
# print(f"With fixed delay of {delay}ns")
# msg = "Hello World"
# channel2 = Channel(name="dchannel", delay=delay)
# channel2.send(msg)
# ns.sim_run()
#
# item , d = channel2.receive()
#
# print(item, d)

# Delay model

from netsquid.components.models.delaymodels  import FixedDelayModel, GaussianDelayModel, FibreDelayModel
from netsquid.components.models.qerrormodels import FibreLossModel

fixed_delay_model = FixedDelayModel(delay=14)
gaussian_model = GaussianDelayModel(delay_mean=5, delay_std=0.5)
fiber_delay = FibreDelayModel()
channel = Channel(name="channel")
channel.properties["length"] = 200000
print(channel.name)

channel.models['delay_model'] = fiber_delay

channel.send("This is a classical message")

loss_model = FibreLossModel()
qchannel = QuantumChannel(name="MyQchannel", length=10, models={'quantum_loss_model': loss_model })

qubit = ns.qubits.create_qubits(1)
qchannel.send(qubit)


ns.sim_run()

print(channel.receive())
print(qchannel.receive())
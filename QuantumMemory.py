import math
import netsquid as ns
from netsquid.components import QuantumMemory
from netsquid.components.models.qerrormodels import DepolarNoiseModel
qmem = QuantumMemory(name="qstorage", num_positions=2)

q0, q1 = ns.qubits.create_qubits(2)
depolar_noise = DepolarNoiseModel(depolar_rate=1e6)


qmem.put(qubits=[q0, q1])
# for mpos in qmem.mem_positions:
#     mpos.models['noise_model'] = depolar_noise


# qmem.operate(ns.H, positions=0)
state, prob = qmem.measure(positions=0, observable=ns.X)

print(state)
print(round(prob[0], 3  ))

print(qmem.peek(0))
import netsquid as ns

q1, q2 = ns.qubits.create_qubits(2)
ns.qubits.combine_qubits([q1, q2])

print(ns.qubits.reduced_dm([q1, q2]))
print(ns.qubits.reduced_dm([q1]))
print(ns.qubits.reduced_dm([q2]))


#Reduce density matrix for Bell State
alice, bob = ns.qubits.create_qubits(2)
ns.qubits.operate(alice, ns.H)
ns.qubits.operate([alice, bob], ns.CX)

print(alice.qstate.qrepr)
print(ns.qubits.reduced_dm([alice, bob]))
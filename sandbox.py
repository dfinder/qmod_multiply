import numpy as np
import qiskit as qs
import qiskit.circuit.library as ql


test= qs.QuantumCircuit(4)
test.append(ql.HGate().control(),qargs=[3,1])

print(test)

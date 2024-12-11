import numpy as np
import qiskit as qs
import qiskit.circuit.library as ql
import qiskit_aer.version


def add_k_fourier(k):
    add_circuit = qs.QuantumCircuit(qs.QuantumRegister(10,"add"))
    for i in range(9,-1,-1):
        add_circuit.append(ql.PhaseGate(k*np.pi/(2**(9-i))),qargs=[i])
    #print(add_circuit.draw())
    return add_circuit
def phase_adder(k,mod): #MAPPING: 0=WORK BIT, 1-10=ACTUAL MATH
    phase_circuit=qs.QuantumCircuit(qs.QuantumRegister(10,"add"),qs.QuantumRegister(1,"adder"))
    phase_circuit.compose(add_k_fourier(k),inplace=True,qubits=range(0,10))
    phase_circuit.compose(add_k_fourier(mod).reverse_ops().inverse(),inplace=True,qubits=range(0,10))
    phase_circuit.append(ql.QFTGate(10).inverse(),qargs=range(0,10))
    phase_circuit.cx(0,10,ctrl_state=1)
    phase_circuit.append(ql.QFTGate(10),qargs=range(0,10))
    phase_circuit.compose(add_k_fourier(mod).control(1,label="Add Mod"),inplace=True,qubits=[10]+list(range(0,10)))
    phase_circuit.compose(add_k_fourier(k).reverse_ops().inverse(),inplace=True,qubits=range(0,10))
    phase_circuit.append(ql.QFTGate(10).inverse(),qargs=range(0,10))
    phase_circuit.append(ql.XGate().control(1,ctrl_state=0),qargs=[0,10])
    phase_circuit.append(ql.QFTGate(10),qargs=range(0,10))
    phase_circuit.compose(add_k_fourier(k),inplace=True,qubits=range(0,10))
    #print(phase_circuit.qregs)
    #print(phase_circuit.draw())
    return phase_circuit
#https://arxiv.org/abs/2311.08555
def mul_out_k_mod(k,mod):
    """Performs :math:`x times k` in the registers wires wires_aux"""
    #swap = qs.AncillaRegister(1)
    multiply_out = qs.QuantumCircuit(20)
    multiply_out.append(ql.QFTGate(10),qargs=[19,9,10,11,12,13,14,15,16,17])
    #print(multiply_out.draw())
    for idx in range(0,9):
        codomain = list(range(9,20))
        new_list = [idx]
        new_list.extend(codomain)
        #print(len(new_list))
        multiply_out.compose(phase_adder(k*(2**(8-idx))%mod,mod).control(1),inplace=True,qubits=new_list)
    multiply_out.append(ql.QFTGate(10).inverse(),qargs=[19,9,10,11,12,13,14,15,16,17])
    return multiply_out

def multiplication(k,mod):
    multiply_circuit = qs.QuantumCircuit(qs.QuantumRegister(9,"multi"),qs.QuantumRegister(10,"add"),qs.QuantumRegister(1,"adder"))
    #multiply_circuit.add_bits(support) multiply: 9 
    #multiply_circuit.add_bits(workspace) add: 10
    #multiply_circuit.add_bits(addition)
    multiply_circuit.compose(mul_out_k_mod(k,mod),inplace=True)
    for x_wire, aux_wire in zip(range(0,9),range(9,19)):
        multiply_circuit.swap(x_wire, aux_wire)
    inv_k = pow(k, -1, mod)
    multiply_circuit.compose(mul_out_k_mod(inv_k,mod).reverse_ops().inverse(),inplace=True)
    return multiply_circuit
#Algorithm in a nutshell
#Hadamard on input(9 wires)
#1 on assist(9 wires)
#11 wires for help.
#qinput = qs.QuantumRegister(9,"Input") #0-8
#support = qs.QuantumRegister(9,"Support") #9-17 #THIS IS WHERE WE DO MULTIPLICATION
#workspace = qs.AncillaRegister(10,"Workspace")#18-27 #THIS IS WHERE WE DO ADDITION
#addition = qs.AncillaRegister(1)28

#extras: 28,29

shors_circuit = qs.QuantumCircuit(qs.QuantumRegister(9,"phase"),qs.QuantumRegister(9,"multi"),qs.AncillaRegister(10,"add"),qs.AncillaRegister(1,"adder"))
shors_circuit.x(17)
shors_circuit.h(range(0,9))
for i,multiplier in enumerate(list(map(lambda x: ((x*8)%299),range(1,10)))):
    shors_circuit.compose(multiplication(multiplier,299).control(1),qubits=[i]+list(range(9,29)),inplace=True)
    shors_circuit.reset(range(18,29))
shors_circuit.append(ql.QFTGate(9).inverse(),range(0,9))
shors_circuit.measure_all()
from qiskit import transpile
from qiskit_aer import AerSimulator
import qiskit_aer
#simulator = AerSimulator()
#print(qiskit_aer.version.get_version_info())

#simulator_gpu = AerSimulator(method='statevector', device='GPU',memory=True)
#
#
#result = simulator.run(circ,shots=100).result()
#print(result.get_memory(circ))

from qiskit_ibm_runtime import QiskitRuntimeService

from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
service = QiskitRuntimeService()
backend = service.least_busy(operational=True, simulator=False)
circ = transpile(shors_circuit, backend)
print(circ.depth())
sampler = Sampler(backend)
job = sampler.run([shors_circuit])
print(f"job id: {job.job_id()}")
result = job.result()
print(result)

def addition()
op_list = []

        if mod == 2 ** len(x_wires):
            op_list.extend(_add_k_fourier(k, x_wires))
        else:
            aux_k = x_wires[0]
            op_list.extend(_add_k_fourier(k, x_wires))

            for op in reversed(_add_k_fourier(mod, x_wires)):
                op_list.append(qml.adjoint(op))

            op_list.append(qml.adjoint(qml.QFT)(wires=x_wires))
            op_list.append(qml.ctrl(qml.PauliX(work_wire), control=aux_k, control_values=1))
            op_list.append(qml.QFT(wires=x_wires))
            op_list.extend(qml.ctrl(op, control=work_wire) for op in _add_k_fourier(mod, x_wires))

            for op in reversed(_add_k_fourier(k, x_wires)):
                op_list.append(qml.adjoint(op))

            op_list.append(qml.adjoint(qml.QFT)(wires=x_wires))
            op_list.append(qml.ctrl(qml.PauliX(work_wire), control=aux_k, control_values=0))
            op_list.append(qml.QFT(wires=x_wires))
            op_list.extend(_add_k_fourier(k, x_wires))

        return op_list

def _mul_out_k_mod(k, x_wires, mod, work_wire_aux, wires_aux):
    """Performs :math:`x \times k` in the registers wires wires_aux"""
    op_list = []

    op_list.append(qml.QFT(wires=wires_aux))
    op_list.append(
        qml.ControlledSequence(qml.PhaseAdder(k, wires_aux, mod, work_wire_aux), control=x_wires)
    )
    op_list.append(qml.adjoint(qml.QFT(wires=wires_aux)))
    return op_list

def multiply_wrapper():
    op_list = []
    if mod != 2 ** len(x_wires):
        work_wire_aux = work_wires[:1]
        wires_aux = work_wires[1:]
        wires_aux_swap = wires_aux[1:]
    else:
        work_wire_aux = None
        wires_aux = work_wires[: len(x_wires)]
        wires_aux_swap = wires_aux
    op_list.extend(_mul_out_k_mod(k, x_wires, mod, work_wire_aux, wires_aux))
    for x_wire, aux_wire in zip(x_wires, wires_aux_swap):
        op_list.append(qml.SWAP(wires=[x_wire, aux_wire]))
    inv_k = pow(k, -1, mod)

    for op in reversed(_mul_out_k_mod(inv_k, x_wires, mod, work_wire_aux, wires_aux)):
        op_list.append(qml.adjoint(op))

    return op_list

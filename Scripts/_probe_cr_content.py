import unreal

CR_PATH = "/Game/Characters/Nami/body1_CtrlRig"
cr = unreal.load_asset(f"{CR_PATH}.body1_CtrlRig")
if not cr:
    unreal.log_error("CR not found")
else:
    h = cr.hierarchy
    keys = h.get_all_keys()
    unreal.log(f"CR elements: {len(keys)}")
    for k in keys[:20]:
        unreal.log(f"  {k.type} {k.name}")
    models = cr.get_all_models()
    unreal.log(f"Graphs: {[m.get_name() for m in models]}")
    ctrl = cr.get_controller_by_name("RigVMModel")
    if ctrl:
        graph = ctrl.get_graph()
        nodes = graph.get_nodes()
        unreal.log(f"Nodes: {len(nodes)}")
        for n in nodes[:15]:
            unreal.log(f"  node {n.get_node_title()}")

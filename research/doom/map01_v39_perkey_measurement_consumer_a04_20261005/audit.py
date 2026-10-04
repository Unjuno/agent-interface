"""Independent raw-row reconstruction of exact owner interval typing."""


def independently_reconstruct(rows):
    if type(rows) is not list or len(rows) != 2:
        raise ValueError("expected one down/up pair")
    found = {}
    cases = ((rows[0], "down", "physical_down_interval"),
             (rows[1], "up", "physical_up_interval"))
    for row, expected_edge, bracket_field in cases:
        if type(row) is not dict:
            raise ValueError("event row must be an object")
        measurement = row.get("physical_key_measurement")
        if type(measurement) is not dict:
            raise ValueError("measurement object missing")
        edge = measurement.get("adapter_edge")
        bracket = measurement.get("bracket")
        if type(edge) is not dict or type(bracket) is not dict:
            raise ValueError("edge/bracket object missing")
        edge_interval = edge.get("interval")
        owner_interval = bracket.get(bracket_field)
        for label, value in (("edge", edge_interval), ("owner", owner_interval)):
            if (type(value) is not list or len(value) != 2
                    or any(type(x) is not int or x < 0 for x in value)
                    or value[0] > value[1]):
                raise ValueError(label + " interval must be two ordered exact integers")
        if edge.get("edge") != expected_edge:
            raise ValueError("edge direction mismatch")
        if owner_interval != edge_interval:
            raise ValueError("owner interval differs from adapter interval")
        found[expected_edge] = list(owner_interval)
    return found

from model import Event, VALID_KINDS

def E(i,session,kind,arrival=None):
    return Event(f'r{i}',session,i,i if arrival is None else arrival,kind,VALID_KINDS[kind],f'ev{i}')

def directed_cases():
    return {
        'independent_progress':[E(0,'A','PROGRESS'),E(1,'B','PROGRESS'),E(2,'A','PROGRESS'),E(3,'B','PROGRESS')],
        'causal_pair':[E(0,'A','NEEDS_DECISION'),E(1,'A','TARGET_LOST')],
        'critical_pair':[E(0,'A','TARGET_LOST'),E(1,'A','LEASE_EXPIRED')],
        'mixed_sessions':[E(0,'B','TARGET_LOST'),E(1,'A','PROGRESS'),E(2,'B','LEASE_EXPIRED'),E(3,'A','GOAL_REACHED')],
        'goal_terminal':[E(0,'A','GOAL_REACHED'),E(1,'A','TERMINAL')],
        'batch_boundary':[E(0,'A','PROGRESS'),E(1,'B','PROGRESS'),E(2,'A','NEEDS_DECISION'),E(3,'B','TARGET_LOST'),E(4,'A','TERMINAL')],
        'metadata':[E(0,'A','PROGRESS',10),E(1,'B','TARGET_LOST',12),E(2,'A','NEEDS_DECISION',15),E(3,'B','PROGRESS',18)],
    }

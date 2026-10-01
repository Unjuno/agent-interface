from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass
class Binding:
    binding_id: str
    generation: str
    dependency: str

@dataclass
class Method:
    method_id: str
    contract: str
    version: str

class Lifecycle:
    def __init__(self, fixture):
        i=fixture['initial']
        self.palette=Binding(**i['palette'])
        self.world=Binding(**i['world'])
        self.method=Method(**i['method'])
        self.effects={}
        self.owned_resources=set()
        self.ledger=[]

    def versions(self):
        return {'palette':self.palette.generation,'world':self.world.generation,
                'method_id':self.method.method_id,'method_version':self.method.version}

    def _record(self, phase, op, evidence_id, before, charge, status, effect_id=None, reason=None):
        row={'phase':phase,'operation':op,'evidence_id':evidence_id,
             'versions_before':before,'versions_after':self.versions(),
             'logical_generation_charge':charge,'status':status,
             'effect_id':effect_id,'reason':reason,
             'owned_resources_after':sorted(self.owned_resources)}
        self.ledger.append(row)
        return row

    def cold(self, receipt):
        before=self.versions()
        ok=(receipt['palette_generation']==self.palette.generation and
            receipt['palette_dependency']==self.palette.dependency and
            receipt['world_generation']==self.world.generation and
            receipt['world_dependency']==self.world.dependency and
            receipt['method_id']==self.method.method_id and receipt['method_version']==self.method.version)
        return self._record('cold','install','cold',before,1,'INSTALLED' if ok else 'COLD_RECEIPT_MISMATCH',reason=None if ok else 'receipt_mismatch')

    def reuse(self, phase, task_id, evidence_id, evidence, requested_world_generation=None):
        before=self.versions()
        if not evidence.get('fresh') or evidence.get('palette_dependency') is None or evidence.get('world_dependency') is None:
            return self._record(phase,'reuse',evidence_id,before,0,'NO_TARGET_AUTHORITY',reason='current_evidence_unavailable')
        if evidence['palette_dependency'] != self.palette.dependency:
            return self._record(phase,'reuse',evidence_id,before,0,'STALE_PALETTE_BINDING',reason='palette_dependency_changed')
        req=requested_world_generation or self.world.generation
        if req != self.world.generation:
            return self._record(phase,'reuse',evidence_id,before,0,'STALE_WORLD_GENERATION',reason='world_generation_changed')
        if evidence['world_dependency'] != self.world.dependency:
            return self._record(phase,'reuse',evidence_id,before,0,'STALE_WORLD_BINDING',reason='world_dependency_changed')
        if task_id in self.effects:
            return self._record(phase,'reuse',evidence_id,before,0,'IDEMPOTENT_REPLAY',effect_id=self.effects[task_id],reason='duplicate_task')
        self.owned_resources={'pointer'}
        effect_id=f'effect:{task_id}'
        self.effects[task_id]=effect_id
        self.owned_resources.clear()
        return self._record(phase,'reuse',evidence_id,before,0,'EFFECT_VERIFIED',effect_id=effect_id)

    def repair(self, phase, receipt, evidence_id, evidence, *, overbroad=False):
        before=self.versions()
        if not evidence.get('fresh') or evidence.get('world_dependency') is None:
            return self._record(phase,'repair',evidence_id,before,0,'REPAIR_REFUSED',reason='current_evidence_unavailable')
        if overbroad:
            return self._record(phase,'repair',evidence_id,before,0,'OVERBROAD_REPAIR_REJECTED',reason='palette_or_method_mutation')
        checks=(receipt['from_world_generation']==self.world.generation and
                receipt['preserve_palette_generation']==self.palette.generation and
                receipt['preserve_method_id']==self.method.method_id and
                receipt['preserve_method_version']==self.method.version and
                receipt['new_world_dependency']==evidence['world_dependency'])
        if not checks:
            return self._record(phase,'repair',evidence_id,before,0,'REPAIR_REFUSED',reason='receipt_or_evidence_mismatch')
        self.world=Binding(self.world.binding_id, receipt['to_world_generation'], receipt['new_world_dependency'])
        return self._record(phase,'repair',evidence_id,before,1,'REPAIR_PROMOTED')

    def snapshot(self):
        return {'palette':asdict(self.palette),'world':asdict(self.world),'method':asdict(self.method),
                'effects':dict(self.effects),'owned_resources':sorted(self.owned_resources),'ledger':list(self.ledger)}

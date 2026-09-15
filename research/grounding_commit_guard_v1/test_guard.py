import copy
import unittest
from guard import Binding, select, descendants


def node(i,b,role,name,children=(),**kw):
    return dict(nodeId=str(i),backendDOMNodeId=b,role={'value':role},name={'value':name},
                childIds=list(map(str,children)),ignored=False,**kw)


def tree():
    return {'nodes':[node(1,10,'RootWebArea','', [2]),node(2,20,'region','Workspace',[3]),
                     node(3,30,'button','Target')]}


class Guards(unittest.TestCase):
    def setUp(self):self.t=tree();self.b=Binding(10,20,30)
    def result(self):return select(self.t,10,self.b)[0]
    def test_valid(self):self.assertEqual(self.result(),'SELECTED')
    def test_document(self):self.assertEqual(select(self.t,11,self.b)[0],'BINDING_CHANGED')
    def test_scope_replaced(self):
        self.t['nodes'][1]['backendDOMNodeId']=21;self.assertEqual(self.result(),'BINDING_CHANGED')
    def test_target_replaced(self):
        self.t['nodes'][2]['backendDOMNodeId']=31;self.assertEqual(self.result(),'TARGET_REPLACED')
    def test_same_name_new_node_baseline_accepts(self):
        self.t['nodes'][2]['backendDOMNodeId']=31
        self.assertEqual(select(self.t,10)[0],'SELECTED')
    def test_renamed(self):
        self.t['nodes'][2]['name']['value']='Cancel';self.assertEqual(self.result(),'TARGET_CARDINALITY')
    def test_role_changed(self):
        self.t['nodes'][2]['role']['value']='link';self.assertEqual(self.result(),'TARGET_CARDINALITY')
    def test_disabled(self):
        self.t['nodes'][2]['properties']=[{'name':'disabled','value':{'value':True}}]
        self.assertEqual(self.result(),'DISABLED')
    def test_ignored(self):
        self.t['nodes'][2]['ignored']=True;self.assertEqual(self.result(),'TARGET_CARDINALITY')
    def test_duplicate_scope(self):
        self.t['nodes'].append(node(4,40,'region','Workspace'));self.assertEqual(self.result(),'SCOPE_CARDINALITY')
    def test_duplicate_inside_scope(self):
        self.t['nodes'][1]['childIds'].append('4');self.t['nodes'].append(node(4,40,'button','Target'))
        self.assertEqual(self.result(),'TARGET_CARDINALITY')
    def test_duplicate_outside_scope(self):
        self.t['nodes'].append(node(4,40,'button','Target'));self.assertEqual(self.result(),'SELECTED')
    def test_missing_not_fallback(self):
        self.t['nodes'][1]['childIds']=[];self.assertEqual(self.result(),'TARGET_CARDINALITY')
    def test_traversal_cycle_terminates(self):
        self.t['nodes'][2]['childIds']=['2'];self.assertEqual(self.result(),'SELECTED')
    def test_inputs_unmodified(self):
        before=copy.deepcopy(self.t);select(self.t,10,self.b);self.assertEqual(self.t,before)
    def test_semantics_unobservable(self):
        # Distinct application meaning with identical AX is intentionally unresolvable.
        self.assertEqual(select(copy.deepcopy(self.t),10,self.b),select(self.t,10,self.b))


if __name__=='__main__':unittest.main(verbosity=2)

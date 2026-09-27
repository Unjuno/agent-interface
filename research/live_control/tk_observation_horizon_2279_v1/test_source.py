import ast
import types
import unittest
import worker

class SourceTests(unittest.TestCase):
    def test_source_and_all_scenarios(self):
        for s in worker.SCENARIOS:
            for p in ('PRECHECK_ONLY','POST_OBSERVATION'):
                tree,digest=worker.program(p,s)
                self.assertEqual(len(digest),64)
                compile(tree,'construction','exec')
    def test_strict_deadline_boundary(self):
        # Evaluate the actual candidate branch AST on exact synthetic time controls.
        tree,_=worker.program('POST_OBSERVATION','fast')
        nodes=[n for n in ast.walk(tree) if isinstance(n,ast.If)
               and isinstance(n.test,ast.Compare) and 'cget' in ast.unparse(n.test)]
        self.assertEqual(len(nodes),1)
        code=compile(ast.fix_missing_locations(ast.Module(body=nodes[0].body[:-1],type_ignores=[])),'branch','exec')
        for value,want in ((.199,'COMPLETED'),(.200,'UNKNOWN'),(.201,'UNKNOWN')):
            env={'time':types.SimpleNamespace(monotonic=lambda:value),'start':0.,'horizon':.2}
            exec(code,env)
            self.assertEqual(env['state'],want)
    def test_one_scientific_branch_change(self):
        legacy,_=worker.program('PRECHECK_ONLY','fast')
        fixed,_=worker.program('POST_OBSERVATION','fast')
        legacy_if=[n for n in ast.walk(legacy) if isinstance(n,ast.If) and 'cget' in ast.unparse(n.test)][0]
        fixed_if=[n for n in ast.walk(fixed) if isinstance(n,ast.If) and 'cget' in ast.unparse(n.test)][0]
        legacy_if.body=fixed_if.body
        self.assertEqual(ast.dump(legacy),ast.dump(fixed))

if __name__=='__main__': unittest.main(verbosity=2)

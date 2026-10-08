import itertools
import unittest
from model import CapabilityState, Request, Route, SideEffect, TextCoverage, choose_route, x11_evidence_profile

ALL_EFFECTS=frozenset(SideEffect)

class ModelTest(unittest.TestCase):
    def test_ascii_transparent_selects_direct(self):
        self.assertEqual(choose_route(x11_evidence_profile(), Request(TextCoverage.ASCII, frozenset())).selected,"direct_keys")
    def test_unicode_transparent_fails_closed(self):
        d=choose_route(x11_evidence_profile(), Request(TextCoverage.UNICODE, frozenset())); self.assertIsNone(d.selected)
        self.assertIn(("clipboard_utf8","side_effect_forbidden:clipboard_content,clipboard_owner,clipboard_targets"), d.rejected)
    def test_unicode_clipboard_side_effect_budget_selects_clipboard(self):
        allowed=frozenset({SideEffect.CLIPBOARD_CONTENT,SideEffect.CLIPBOARD_OWNER,SideEffect.CLIPBOARD_TARGETS})
        self.assertEqual(choose_route(x11_evidence_profile(), Request(TextCoverage.UNICODE,allowed)).selected,"clipboard_utf8")
    def test_keymap_not_selected_when_exact_unproven(self):
        d=choose_route(x11_evidence_profile(), Request(TextCoverage.UNICODE,ALL_EFFECTS)); self.assertEqual(d.selected,"clipboard_utf8")
        self.assertIn(("keymap_remap","exact_semantics_unproven"), d.rejected)
    def test_unknown_routes_never_selected(self):
        d=choose_route(x11_evidence_profile(), Request(TextCoverage.UNICODE,ALL_EFFECTS)); self.assertNotIn(d.selected,{"accessibility_set_value","native_ime"})
    def test_permission_required_explains_failure(self):
        r=Route("native_ime",CapabilityState.PERMISSION_REQUIRED,frozenset({TextCoverage.UNICODE}),frozenset(),True,"input-monitoring")
        d=choose_route([r],Request(TextCoverage.UNICODE,frozenset())); self.assertEqual(d.rejected,(("native_ime","permission_required:input-monitoring"),))
    def test_accessibility_wins_when_supported_exact_and_allowed(self):
        routes=list(x11_evidence_profile()); routes[3]=Route("accessibility_set_value",CapabilityState.SUPPORTED,frozenset({TextCoverage.UNICODE}),frozenset({SideEffect.ACCESSIBILITY_WRITE}),True)
        allowed=frozenset({SideEffect.ACCESSIBILITY_WRITE,SideEffect.CLIPBOARD_CONTENT,SideEffect.CLIPBOARD_OWNER,SideEffect.CLIPBOARD_TARGETS})
        self.assertEqual(choose_route(routes,Request(TextCoverage.UNICODE,allowed)).selected,"accessibility_set_value")
    def test_lower_side_effect_cost_beats_route_rank(self):
        routes=[Route("clipboard_utf8",CapabilityState.SUPPORTED,frozenset({TextCoverage.UNICODE}),frozenset({SideEffect.CLIPBOARD_CONTENT,SideEffect.CLIPBOARD_OWNER}),True),Route("native_ime",CapabilityState.SUPPORTED,frozenset({TextCoverage.UNICODE}),frozenset({SideEffect.IME_STATE}),True)]
        self.assertEqual(choose_route(routes,Request(TextCoverage.UNICODE,ALL_EFFECTS)).selected,"native_ime")
    def test_global_keymap_is_riskier_than_clipboard_even_if_exact(self):
        routes=list(x11_evidence_profile()); routes[2]=Route("keymap_remap",CapabilityState.SUPPORTED,routes[2].coverage,routes[2].side_effects,True)
        self.assertEqual(choose_route(routes,Request(TextCoverage.UNICODE,ALL_EFFECTS)).selected,"clipboard_utf8")
    def test_duplicate_names_fail(self):
        r=Route("direct_keys",CapabilityState.SUPPORTED,frozenset({TextCoverage.ASCII}),frozenset(),True)
        with self.assertRaises(ValueError): choose_route([r,r],Request(TextCoverage.ASCII,frozenset()))
    def test_monotonic_side_effect_restriction_exhaustive(self):
        routes=x11_evidence_profile(); effects=list(SideEffect)
        budgets=[frozenset(e for e,b in zip(effects,bits) if b) for bits in itertools.product((False,True),repeat=len(effects))]
        for cov in TextCoverage:
            for b in budgets:
                d=choose_route(routes,Request(cov,b))
                if d.selected:
                    route=next(r for r in routes if r.name==d.selected); self.assertTrue(route.side_effects <= b)
    def test_all_state_combinations_fail_closed_when_not_supported(self):
        for state in CapabilityState:
            r=Route("native_ime",state,frozenset({TextCoverage.UNICODE}),frozenset(),state is CapabilityState.SUPPORTED)
            d=choose_route([r],Request(TextCoverage.UNICODE,frozenset())); self.assertEqual(d.selected=="native_ime", state is CapabilityState.SUPPORTED)

if __name__=='__main__':unittest.main()

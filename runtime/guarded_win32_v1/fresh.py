"""Refresh an observational reference; never dispatches input."""
from .reference import ReferencedWin32Observation

class FreshWin32Reference(ReferencedWin32Observation):

    def resolve_fresh(self, alias, offset):
        if self.review_required:
            raise ValueError('association review required')
        binding = self._binding()
        if binding != self._initial:
            self.review_required = True
            raise ValueError('association changed before refresh')
        g = binding['geometry']
        row = self.observe([0, 0, g['width'], g['height']])
        result = self.resolve(alias, offset, row['sequence'])
        if self._binding() != binding:
            self.review_required = True
            raise ValueError('association changed during resolution')
        return result

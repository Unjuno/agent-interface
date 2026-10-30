import unittest
from pair_saved_oracle import score_saved

def document(rows):
 return ("<office:document xmlns:office='urn:oasis:names:tc:opendocument:xmlns:office:1.0' xmlns:table='urn:oasis:names:tc:opendocument:xmlns:table:1.0' xmlns:text='urn:oasis:names:tc:opendocument:xmlns:text:1.0'><office:body><office:spreadsheet><table:table>"+rows+"</table:table></office:spreadsheet></office:body></office:document>").encode()
def row(value,extra=''):
 return "<table:table-row><table:table-cell office:value-type='float' office:value='%s' %s><text:p>%s</text:p></table:table-cell></table:table-row>"%(value,extra,value)
class SavedPairTests(unittest.TestCase):
 def test_two_numbers_are_the_only_populated_cells(self):
  self.assertTrue(score_saved(document(row('731')+row('864')))['pass_effect'])
 def test_wrong_or_extra_values_are_not_success(self):
  for rows in (row('731')+row('863'),row('731')+row('864')+row('9')):
   with self.subTest(rows=rows):self.assertFalse(score_saved(document(rows))['pass_effect'])
 def test_formula_is_not_a_plain_number(self):
  self.assertFalse(score_saved(document(row('731',"table:formula='of:=1+730'")+row('864')))['pass_effect'])
 def test_repeated_populated_cell_is_not_success(self):
  self.assertFalse(score_saved(document(row('731',"table:number-columns-repeated='2'")+row('864')))['pass_effect'])
 def test_malformed_xml_is_unknown(self):
  self.assertIsNone(score_saved(b'<broken')['pass_effect'])

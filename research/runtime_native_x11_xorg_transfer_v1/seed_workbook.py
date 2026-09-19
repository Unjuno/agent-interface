#!/usr/bin/env python3
import argparse
from openpyxl import Workbook
p=argparse.ArgumentParser(); p.add_argument('--out',required=True); a=p.parse_args()
w=Workbook(); w.active.title='Sheet1'; w.save(a.out)

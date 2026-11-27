"""Bind explicit Calc OCR cue to guarded compiled-graph perception.

The context callback supplies graph predicates and independently established
blank evidence for the same capture. This adapter does not establish capture
freshness, target authority, OCR time bounds, or durable workbook effects.
"""
from research.live_control.calc_ocr_pair_cue_v1 import classify_pair
from research.live_control.calc_compiled_method_v1 import compile_calc_method
from runtime.core_v1.compiled_gui import validate


def make_ocr_calc_method(**kwargs):
    """Build the existing Calc graph with a guard-rechecked blank predicate."""
    graph = compile_calc_method(**kwargs)
    graph['predicates'].append('cells_blank')
    graph['symbols']['sheet']['dependencies'].append('cells_blank')
    graph['method']['states']['initial']['branches'][0]['when']['cells_blank'] = True
    return validate(graph)



def make_perception(context_perceive, read_ocr, *, expected):
    """Construct a callback returning declared Calc graph predicates.

    A confidently different OCR value is *not* evidence that cells are blank.
    OCR and blank evidence that contradict each other fail closed. Callback
    implementations must observe the same supplied native capture and image.
    """
    if not callable(context_perceive) or not callable(read_ocr):
        raise ValueError("explicit context and OCR callbacks required")
    classify_pair('', '', expected=expected)  # validate before any graph input

    def perceive(native, image):
        result = context_perceive(native, image)
        if type(result) is not tuple or len(result) != 2:
            raise ValueError("context must return (predicate mapping, blank evidence)")
        predicates, blank = result
        if type(predicates) is not dict or {'cells_match', 'cells_blank'} & predicates.keys():
            raise ValueError("context must not supply OCR-owned predicates")
        if blank is not None and type(blank) is not bool:
            raise ValueError("blank evidence must be true, false, or unknown")
        predicates = dict(predicates)
        try:
            evidence = read_ocr(native, image)
            if type(evidence) is not tuple or len(evidence) != 2 or any(type(x) is not str for x in evidence):
                raise ValueError("two OCR TSV strings required")
            cue = classify_pair(*evidence, expected=expected)
        except Exception:
            predicates['cells_match'] = 'unknown'
            predicates['cells_blank'] = False
            return predicates
        predicates['cells_blank'] = cue == 'unknown' and blank is True
        if cue == 'filled' and blank is not True:
            predicates['cells_match'] = True
        elif cue == 'unknown' and blank is True:
            predicates['cells_match'] = False
        else:
            predicates['cells_match'] = 'unknown'
        return predicates

    return perceive

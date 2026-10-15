import json
import math
import pytest
from pydantic import ValidationError
from optics_portfolio.parameters import Parameter,ParameterConfig,ParameterError,evaluate_config,load_config,LABEL

def literal(value=2.,unit='mm',**kwargs):
    return dict(value=value,unit=unit,source='algorithmic_input',description='Manufactured input',**kwargs)

def expr(s):return dict(expression=s,unit='SI',source='derived',description='Manufactured expression')
def config(params):return ParameterConfig(provenance=LABEL,parameters=params)

@pytest.mark.parametrize('unit,factor',[('m',1),('mm',1e-3),('um',1e-6),('nm',1e-9),('deg',math.pi/180),('rad',1),('1',1)])
def test_unit_conversion(unit,factor):
    r=evaluate_config(config({'a':literal(2.,unit)}));assert r['values_si']['a']==pytest.approx(2*factor)

def test_out_of_order_dependencies_and_math():
    r=evaluate_config(config({'result':expr('sqrt(a * a) + cos(angle)'), 'angle':literal(180.,'deg'),'a':literal(8.,'mm')}))
    assert r['values_si']['result']==pytest.approx(.008-1)
    assert r['evaluation_order'].index('a')<r['evaluation_order'].index('result')

@pytest.mark.parametrize('p',[
    {**literal(), 'source':'unknown'}, {**literal(), 'source':'paper_value'},
    {**literal(), 'source':'inferred'}, {**literal(), 'value':float('nan')},
    {**literal(), 'value':True}, {**literal(), 'value':'2'},
    {**literal(), 'unit':'furlong'}, {**literal(), 'extra':1},
    {**literal(), 'expression':'1'}, {**literal(), 'description':' '},
    {**expr('1'), 'unit':'mm'}, {**expr('1'), 'source':'algorithmic_input'},
])
def test_bad_contracts(p):
    with pytest.raises(ValidationError):Parameter.model_validate(p)

def test_source_metadata():
    Parameter.model_validate({**literal(),'source':'paper_value','reference':'TEST ONLY: fictitious citation metadata'})
    Parameter.model_validate({**literal(),'source':'inferred','uncertainty_note':'TEST ONLY: artificial uncertainty'})

@pytest.mark.parametrize('s',[
    "__import__('os')",'a.real','[x for x in a]','(lambda: 1)()',
    'sin(x=1)','sin(1,2)','2**1000','2**0.5','sqrt(-1)','1/0','1e101',
    'True','1j','[1,2]','9'*260,'abs('*15+'1'+')'*15,
])
def test_expression_rejection(s):
    with pytest.raises((ParameterError,ValidationError)):evaluate_config(config({'a':expr(s)}))

def test_unknown_and_cycles():
    with pytest.raises(ParameterError,match='unknown'):evaluate_config(config({'x':expr('missing+1')}))
    with pytest.raises(ParameterError,match='cyclic'):evaluate_config(config({'x':expr('y'),'y':expr('x')}))

@pytest.mark.parametrize('name',['_hidden','pi','sin','bad-name','é'])
def test_bad_name(name):
    with pytest.raises(ValidationError):config({name:literal()})

def test_unsupported_provenance():
    with pytest.raises(ValidationError):ParameterConfig(provenance='REAL_RESEARCH',parameters={'a':literal()})

def test_duplicate_json_and_size(tmp_path):
    p=tmp_path/'duplicate.json';p.write_text('{"a":1,"a":2}')
    with pytest.raises(ParameterError,match='duplicate'):load_config(p)
    q=tmp_path/'big.json';q.write_text(' '*65537)
    with pytest.raises(ParameterError,match='64 KiB'):load_config(q)

def test_json_round_trip(tmp_path):
    p=tmp_path/'valid.json';c=config({'a':literal(),'b':expr('a**2')})
    p.write_text(c.model_dump_json(),encoding='utf-8')
    assert evaluate_config(load_config(p))['values_si']['b']==pytest.approx(4e-6)

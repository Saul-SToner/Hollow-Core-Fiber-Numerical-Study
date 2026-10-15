"""Generic toy-parameter contracts and bounded AST interpretation; no eval()."""
import ast
from enum import Enum
import json
import math
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

LABEL = 'ALGORITHMIC_FIXTURE_NOT_COMSOL'
FACTORS = {'1':1., 'm':1., 'mm':1e-3, 'um':1e-6, 'nm':1e-9,
           'rad':1., 'deg':math.pi/180, 'SI':1.}
FUNCTIONS = {'sqrt':math.sqrt, 'sin':math.sin, 'cos':math.cos, 'abs':abs}
MAX_VALUE = 1e100


class ParameterError(ValueError):
    pass


class Source(str, Enum):
    ALGORITHMIC_INPUT='algorithmic_input'
    DERIVED='derived'
    PAPER_VALUE='paper_value'
    INFERRED='inferred'
    NUMERICAL_SETTING='numerical_setting'


class Parameter(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True,allow_inf_nan=False)
    value: float | None = Field(default=None, strict=True)
    expression: str | None = Field(default=None,min_length=1,max_length=256)
    unit: str
    source: Source
    description: str = Field(min_length=1,max_length=256)
    reference: str | None = Field(default=None,min_length=1,max_length=256)
    uncertainty_note: str | None = Field(default=None,min_length=1,max_length=256)

    @field_validator('description','expression','reference','uncertainty_note')
    @classmethod
    def nonblank(cls,v):
        if v is not None and not v.strip():raise ValueError('blank text is not allowed')
        return v

    @model_validator(mode='after')
    def semantics(self):
        if (self.value is None)==(self.expression is None):
            raise ValueError('exactly one of value/expression required')
        if self.unit not in FACTORS:raise ValueError('unsupported unit')
        if self.expression is not None:
            if self.unit!='SI' or self.source!=Source.DERIVED:
                raise ValueError('expressions consume SI-valued names; unit=SI and source=derived required')
        elif self.unit=='SI' or self.source==Source.DERIVED:
            raise ValueError('literal needs explicit unit and non-derived source')
        if self.source==Source.PAPER_VALUE and not self.reference:
            raise ValueError('paper_value requires reference metadata')
        if self.source==Source.INFERRED and not self.uncertainty_note:
            raise ValueError('inferred source requires uncertainty_note')
        return self


class ParameterConfig(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True)
    provenance: str
    parameters: dict[str,Parameter]

    @model_validator(mode='after')
    def check_config(self):
        if self.provenance!=LABEL:raise ValueError('only algorithmic fixtures accepted')
        if not 1<=len(self.parameters)<=64:raise ValueError('need 1..64 parameters')
        for name in self.parameters:
            if (not name.isascii() or not name.isidentifier() or not name[0].isalpha()
                or len(name)>48 or name in set(FUNCTIONS)|{'pi'}):
                raise ValueError(f'invalid/reserved parameter name: {name}')
        return self


def _unique(pairs):
    obj={}
    for k,v in pairs:
        if k in obj:raise ParameterError(f'duplicate JSON key: {k}')
        obj[k]=v
    return obj


def load_config(path):
    data=Path(path).read_bytes()
    if len(data)>65536:raise ParameterError('config exceeds 64 KiB')
    return ParameterConfig.model_validate(json.loads(data.decode('utf-8'),object_pairs_hook=_unique))


def _parse(text):
    try:tree=ast.parse(text,mode='eval')
    except (SyntaxError,RecursionError) as exc:raise ParameterError('invalid expression syntax') from exc
    if sum(1 for _ in ast.walk(tree))>64:raise ParameterError('AST exceeds 64 nodes')
    deps=set()
    def visit(node,depth=0):
        if depth>12:raise ParameterError('expression nesting exceeds 12')
        if isinstance(node,ast.Constant):
            if type(node.value) not in (int,float):raise ParameterError('real numeric literal required')
        elif isinstance(node,ast.Name):
            if node.id not in {'pi'}:deps.add(node.id)
        elif isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            visit(node.operand,depth+1)
        elif isinstance(node,ast.BinOp) and isinstance(node.op,(ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Pow)):
            visit(node.left,depth+1);visit(node.right,depth+1)
        elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in FUNCTIONS and len(node.args)==1 and not node.keywords:
            visit(node.args[0],depth+1)
        else:raise ParameterError('unsupported expression node/function')
    visit(tree.body)
    return tree.body,deps


def _bounded(v):
    try:v=float(v)
    except (ValueError,TypeError,OverflowError) as exc:raise ParameterError('non-real numeric result') from exc
    if not math.isfinite(v) or abs(v)>MAX_VALUE:raise ParameterError('result outside finite magnitude limit 1e100')
    return v


def _value(node,known):
    if isinstance(node,ast.Constant):return _bounded(node.value)
    if isinstance(node,ast.Name):return math.pi if node.id=='pi' else known[node.id]
    if isinstance(node,ast.UnaryOp):
        v=_value(node.operand,known);return v if isinstance(node.op,ast.UAdd) else -v
    if isinstance(node,ast.Call):return _bounded(FUNCTIONS[node.func.id](_value(node.args[0],known)))
    a,b=_value(node.left,known),_value(node.right,known)
    if isinstance(node.op,ast.Add):v=a+b
    elif isinstance(node.op,ast.Sub):v=a-b
    elif isinstance(node.op,ast.Mult):v=a*b
    elif isinstance(node.op,ast.Div):v=a/b
    else:
        if not b.is_integer() or abs(b)>8:raise ParameterError('power exponent must be integer in [-8,8]')
        v=a**int(b)
    return _bounded(v)


def evaluate_config(config):
    if not isinstance(config,ParameterConfig):raise ParameterError('validated ParameterConfig required')
    trees={};deps={}
    for name,p in config.parameters.items():
        if p.expression is None:deps[name]=set()
        else:
            trees[name],deps[name]=_parse(p.expression)
            missing=deps[name]-config.parameters.keys()
            if missing:raise ParameterError(f'{name}: unknown symbols {sorted(missing)}')
    known={};order=[]
    while len(known)<len(config.parameters):
        ready=[n for n in config.parameters if n not in known and deps[n]<=known.keys()]
        if not ready:raise ParameterError('cyclic parameter dependencies')
        for name in ready:
            p=config.parameters[name]
            try:
                v=_bounded(p.value*FACTORS[p.unit]) if p.value is not None else _value(trees[name],known)
            except (ArithmeticError,ValueError) as exc:raise ParameterError(f'{name}: {exc}') from exc
            known[name]=v;order.append(name)
    return {'provenance':LABEL,'status':'PASS','values_si':known,'evaluation_order':order,
            'note':'Numeric SI conversion only; no general dimensional inference or Maxwell geometry validation.'}

"""Build the editable SVG workflow example using only Python's standard library."""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
parts = ['''<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="1190" viewBox="0 0 1180 1190" role="img" aria-labelledby="title description">
<title id="title">Logic puzzle recontextualisation workflow</title>
<desc id="description">An actor selection puzzle becomes a garden plant selection puzzle through a one-to-one mapping. GPT-4o generates the adaptation, Qwen judges it, and this example passes on its first attempt. A separate dashed feedback branch shows refinement for rejected outputs. Both examples select four of seven entities, preserve three logical constraints, and have the correct option B.</desc>
<defs>
 <marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0 0 L9 4.5 L0 9 Z" fill="#323b45"/></marker>
 <marker id="optionalArrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0 0 L9 4.5 L0 9 Z" fill="#7d877f"/></marker>
 <style>text{font-family:Arial,Helvetica,sans-serif;fill:#18212b} .muted{fill:#52616b} .small{font-size:17px} .body{font-size:21px} .label{font-size:19px;font-weight:700} .heading{font-size:26px;font-weight:700} .node{font-size:20px;font-weight:700} .green{fill:#24703a}</style>
</defs>
<rect width="1180" height="1190" rx="0" fill="#ffffff"/>
''']


def rect(x, y, w, h, fill, stroke='#40464d', radius=14, **attrs):
    extra = ' '.join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="1.4" {extra}/>')


def text(x, y, value, css='body', anchor='start'):
    parts.append(f'<text x="{x}" y="{y}" class="{css}" text-anchor="{anchor}">{escape(value)}</text>')


def path(value, optional=False):
    color = '#7d877f' if optional else '#323b45'
    dash = 'stroke-dasharray="6 5"' if optional else ''
    marker = 'optionalArrow' if optional else 'arrow'
    parts.append(f'<path d="{value}" fill="none" stroke="{color}" stroke-width="1.8" {dash} marker-end="url(#{marker})"/>')



text(52, 49, 'Same logic. A new narrative.', 'heading')
text(52, 80, 'Generate a new setting, verify the mapping, and refine rejected outputs.', 'body muted')
# Explicit entity correspondence above the generator output.
rect(436, 110, 250, 63, '#fff0d8', '#c77812', 10)
text(561, 136, 'P→A   Q→B   R→C   S→D', 'small', 'middle')
text(561, 159, 'T→E   U→F   V→G', 'small', 'middle')
# Main workflow.
nodes = [(52, 130, '#dceafe', '#5c83cb', 'Original', 'puzzle'),
         (230, 150, '#e4d7ee', '#9371b0', 'Generator', 'GPT-4o'),
         (436, 172, '#ffe6c6', '#c77812', 'Adapted', 'puzzle'),
         (665, 170, '#e4d7ee', '#9371b0', 'Judge', 'Qwen3.5:9B'),
         (891, 237, '#f1f2f2', '#40464d', 'PASS', 'Accepted in round 1')]
for x, w, fill, stroke, title, subtitle in nodes:
    rect(x, 203, w, 81, fill, stroke, 13)
    text(x+w/2, 234, title, 'node' + (' green' if title=='PASS' else ''), 'middle')
    text(x+w/2, 261, subtitle, 'small', 'middle')
for start,end in [(182,230),(380,436),(608,665),(835,891)]:path(f'M{start} 244 H{end-3}')
# Optional feedback path is separate from this example's actual round-1 acceptance.
rect(436, 337, 230, 58, '#c9e990', '#7eaa48', 12)
text(551, 373, 'Refine with feedback', 'label', 'middle')
path('M750 284 V366 H671', optional=True)
path('M436 366 H305 V289', optional=True)
text(775, 316, 'If rejected', 'small muted')
text(551, 421, 'Dashed branch: used only for failed generations', 'small muted', 'middle')
parts.append('<line x1="52" y1="445" x2="1128" y2="445" stroke="#bdc6cc" stroke-width="1"/>')
# Two aligned example panels.
for x, fill, stroke, heading, domain in [(52,'#efffeb','#3a91b2','Original puzzle','Benefit program · actors'),(608,'#fff0e9','#555b61','Adapted puzzle','Garden plot · plants')]:
    rect(x, 470, 520, 613, fill, stroke, 30)
    text(x+26, 512, heading, 'heading')
    text(x+26, 544, domain, 'body muted')
    text(x+26, 585, 'Select exactly 4 of 7.', 'label')
# Entity tokens.
for x, labels in [(78,list('PQRSTUV')),(634,list('ABCDEFG'))]:
    for i,label in enumerate(labels):
        rect(x+i*64, 607, 51, 39, '#ffffff', '#a7b4b8', 6)
        text(x+i*64+25.5, 634, label, 'label', 'middle')
# The aligned three constraints are concise paraphrases of the stored pair.
for x, items in [(78,[('1. Exactly one of P or T is selected.',),('2. If T is selected, Q is selected.',),('3. If U is selected,', '    neither P nor R is selected.')]),(634,[('1. Exactly one of A or E is selected.',),('2. If E is selected, B is selected.',),('3. If F is selected,', '    neither A nor C is selected.')])]:
    text(x, 689, 'Constraints', 'label')
    for y, lines in zip([724,768,812],items):
        for j,line in enumerate(lines):text(x, y+27*j, line, 'body')
for x, condition, entities, answer_name, chain in [(78,'U',list('PQRSV'),'Q','U → not P → T → Q'),(634,'F',list('ABCDG'),'B','F → not A → E → B')]:
    text(x, 889, 'Question', 'label')
    text(x, 922, f'If {condition} is selected, which must also', 'body')
    text(x, 949, 'be selected?', 'body')
    for i,(option,entity) in enumerate(zip('ABCDE',entities)):
        fill='#dcf0d7' if option=='B' else '#ffffff'
        rect(x+i*92, 972, 82, 36, fill, '#a7b4b8', 5)
        text(x+i*92+41, 997, f'({option}) {entity}', 'small', 'middle')
    text(x, 1041, f'Correct option: B  ·  {answer_name}', 'label green')
    text(x+245, 1069, chain, 'small muted', 'middle')
text(590, 1125, '7→7 entities     ·     4→4 selections     ·     3→3 constraints     ·     Same answer option', 'label', 'middle')
text(590, 1158, 'Illustrative pair: puzzle 113, Q1. The recorded judge accepted the adaptation on its first attempt.', 'small muted', 'middle')
parts.append('</svg>')
path = ROOT / 'assets' / 'recontextualisation_workflow.svg'
path.parent.mkdir(exist_ok=True)
path.write_text('\n'.join(parts)+'\n', encoding='utf-8')
print(path)

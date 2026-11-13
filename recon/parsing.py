"""Deterministic parsers; never extract verdicts or answers from hidden reasoning."""
import json
import re


def strip_thinking(text):
    text = re.sub(r'<(?:gen_think|think)>.*?</(?:gen_think|think)>', '', text, flags=re.S | re.I)
    # Truncated opening thinking blocks contain no final answer.
    return re.split(r'<(?:gen_think|think)>', text, flags=re.I)[0].strip()


def block(text, tag):
    match = re.search(rf'<{tag}>(.*?)</{tag}>', strip_thinking(text), re.S | re.I)
    return match.group(1).strip() if match else ''


def parse_generation(text):
    return {tag: block(text, tag) for tag in ('target_domain', 'mapping', 'adapted_puzzle')}


def parse_json(text):
    clean = strip_thinking(text).strip()
    clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', clean, flags=re.I)
    value = json.loads(clean)
    if not isinstance(value, dict):
        raise ValueError('Expected a JSON object')
    return value


def parse_verdict(text):
    value = parse_json(text)
    if value.get('format_check') not in ('PASS', 'FAIL'):
        raise ValueError('Invalid format_check')
    if type(value.get('logical_equivalence_confirmed')) is not bool or not isinstance(value.get('feedback'), str):
        raise ValueError('Invalid verdict schema')
    if (value['format_check'] == 'PASS') != value['logical_equivalence_confirmed']:
        raise ValueError('Inconsistent verdict')
    return value


def answer(text):
    clean = strip_thinking(str(text))
    # Explicit final-answer markers take priority; never choose an arbitrary A-E in prose.
    patterns = [r'<answer>\s*\[?([A-E])\]?\s*</answer>',
                r'(?:Final\s+answer|Answer)\s*:\s*\**\[?([A-E])\b',
                r'<format>\s*\[([A-E])\]\s*</format>']
    for pattern in patterns:
        matches = re.findall(pattern, clean, flags=re.I)
        if matches:
            return matches[-1].upper()
    match = re.fullmatch(r'\s*\[?([A-E])\]?[.)]?\s*', clean, re.I)
    return match.group(1).upper() if match else None

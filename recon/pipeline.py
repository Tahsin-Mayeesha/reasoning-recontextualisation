"""Resumable experiment stages with private run manifests and round-level traces."""
import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path
from .data import KEYS, validate
from .parsing import answer, parse_generation, parse_verdict, parse_json
from .providers import Client

ROOT = Path(__file__).resolve().parent.parent


def prompt(name):
    path = ROOT / 'prompts' / (name + '.txt')
    return path.read_text(encoding='utf-8')


def key(row):
    return tuple(str(row[c]) for c in KEYS + (['adaptation_id'] if 'adaptation_id' in row else []))


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def run(frame, config, output, stage='adapt', mode='zs', resume=False, client_factory=Client):
    if stage not in ('adapt', 'solve', 'audit-answer', 'audit-judge'):
        raise ValueError('Unknown stage')
    if config.get('max_iterations', 3) not in (1, 2, 3):
        raise ValueError('max_iterations must be 1-3 total attempts')
    if config.get('judge_parse_retries', 3) < 1:
        raise ValueError('judge_parse_retries must be positive')
    validate(frame, sample=stage in ('adapt', 'solve'))
    names = (['generator', 'judge'] if stage == 'adapt' else
             [{'zs': 'zero_shot', 'cot': 'cot'}[mode]] if stage == 'solve' else
             ['answer_audit' if stage == 'audit-answer' else 'judge_audit'])
    signature = {'stage': stage, 'mode': mode, 'config': config,
                 'input_sha256': hashlib.sha256(frame.to_json(orient='records').encode()).hexdigest(),
                 'prompt_sha256': {name: hashlib.sha256(prompt(name).encode()).hexdigest() for name in names}}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = Path(str(output) + '.manifest.json')
    if output.exists() or manifest.exists():
        if not resume:
            raise FileExistsError('Output already exists; use --resume with the identical input/configuration')
        if not manifest.exists() or json.loads(manifest.read_text(encoding='utf-8')) != signature:
            raise ValueError('Resume input, configuration, stage, or prompt mismatch')
    records = []
    if output.exists():
        for line in output.read_text(encoding='utf-8').splitlines():
            records.append(json.loads(line))
        done = {key(r) for r in records}
        if len(done) != len(records):
            raise ValueError('Duplicate checkpoint keys')
    else:
        done = set()
    write_json(manifest, signature)
    generator = client_factory(config['generator'])
    judge = client_factory(config['judge']) if stage == 'adapt' else None
    for _, row in frame.iterrows():
        record = row.to_dict()
        if key(record) in done:
            continue
        try:
            if stage == 'adapt':
                record.update(adapt(record, generator, judge, config))
            elif stage == 'solve':
                reply = generator.call(prompt(names[0]), str(record['Sample']))
                record.update(Raw_Output=reply.text, Reasoning=reply.reasoning,
                              Model_Answer=answer(reply.text), finish_reason=reply.finish_reason)
            else:
                if stage == 'audit-answer':
                    user = f"Raw output:\n{record.get('Raw_Output', '')}\n\nReasoning:\n{record.get('Reasoning', '')}"
                else:
                    user = (f"Adapted puzzle:\n{record.get('final_adapted_puzzle', '')}\n\n"
                            f"Judge verdict:\n{record.get('final_judge_verdict', '')}\n\n"
                            f"Judge think trace:\n{record.get('final_judge_think_trace', '')}")
                reply = generator.call(prompt(names[0]), user)
                record['audit_raw_output'] = reply.text
                # Audit results are additional fields, never replacements for primary judgments.
                if stage == 'audit-answer':
                    value = reply.text.strip().upper()
                    record['Audited_Answer'] = value if value in list('ABCDE') + ['NONE'] else None
                else:
                    record['judge_audit'] = parse_json(reply.text)
            record['execution_status'] = 'complete'
        except Exception as exc:
            # Keep a durable failed row. Do not leak SDK exception strings, URLs, or credentials.
            record['execution_status'] = 'error'
            record['error_type'] = type(exc).__name__
        records.append(record)
        # Atomic full checkpoint prevents a partial trailing JSON record on interruption.
        temporary = Path(str(output) + '.tmp')
        temporary.write_text(''.join(json.dumps(r, ensure_ascii=False, default=str) + '\n' for r in records), encoding='utf-8')
        os.replace(temporary, output)
        done.add(key(record))
    return records


def adapt(row, generator, judge, config):
    sample = row['Sample']
    maximum = config.get('max_iterations', 3)
    user = ('Adapt the following self-contained logic-puzzle question unit.\n'
            'Follow the four-step procedure in your system prompt.\n\n'
            f'<original_puzzle>\n{sample}\n</original_puzzle>')
    rounds = []
    verdict = {}
    parsed = {}
    outcome = 'not_equivalent'
    for iteration in range(1, maximum + 1):
        try:
            generated = generator.call(prompt('generator'), user)
        except Exception as exc:
            rounds.append({'iteration': iteration, 'generator_error': type(exc).__name__})
            outcome = 'generation_failed'
            break
        parsed = parse_generation(generated.text)
        judge_user = f'<original_puzzle>\n{sample}\n</original_puzzle>\n\n' + '\n\n'.join(
            f'<{tag}>\n{parsed[tag] or "(no " + tag + " found)"}\n</{tag}>'
            for tag in ['target_domain', 'mapping', 'adapted_puzzle'])
        attempt_logs = []
        verdict = {'error': 'judge_parse_exhausted', 'logical_equivalence_confirmed': None}
        for attempt in range(config.get('judge_parse_retries', 3)):
            try:
                judged = judge.call(prompt('judge'), judge_user)
            except Exception as exc:
                attempt_logs.append({'error_type': type(exc).__name__})
                verdict['error'] = 'judge_call_failed'
                break
            attempt_logs.append(asdict(judged))
            try:
                verdict = parse_verdict(judged.text)
                break
            except (ValueError, TypeError):
                continue
        # An invalid/incomplete generation cannot be promoted by a spurious PASS.
        if verdict.get('logical_equivalence_confirmed') is True and not all(parsed.values()):
            verdict = {'format_check': 'FAIL', 'logical_equivalence_confirmed': False,
                       'feedback': 'STRUCTURE: MISSING adaptation/domain/mapping', 'local_structure_override': True}
        rounds.append({'iteration': iteration, 'generator': asdict(generated), 'parsed': parsed,
                       'judge_attempts': attempt_logs, 'verdict': verdict})
        if verdict.get('error'):
            outcome = 'judge_failed'
            break
        if verdict['logical_equivalence_confirmed'] is True:
            outcome = 'equivalent'
            break
        user = (f'Refinement attempt {iteration + 1} of {maximum}. Previous adaptation FAILED.\n\n'
                f"<judge_feedback>\nFormat check : {verdict.get('format_check', 'FAIL')}\nFailures     : {verdict.get('feedback', '')}\n</judge_feedback>\n\n"
                f'<previous_output>\n{generated.text}\n</previous_output>\n\n'
                f'<original_puzzle>\n{sample}\n</original_puzzle>\n\n'
                'Fix every failing item. Keep domain or choose a new one.\n'
                'Output ONLY: <target_domain> <mapping> <adapted_puzzle>')
    result = {'rounds': rounds, 'final_outcome': outcome,
              'final_equivalence': True if outcome == 'equivalent' else False if outcome == 'not_equivalent' else None,
              'iterations_used': len(rounds), 'final_adapted_puzzle': parsed.get('adapted_puzzle', ''),
              'final_target_domain': parsed.get('target_domain', ''), 'final_mapping': parsed.get('mapping', ''),
              'final_judge_verdict': verdict, 'generator_model': generator.model, 'judge_model': judge.model}
    # Keep flat fields for historical analysis notebooks as well as complete nested traces.
    for r in rounds:
        prefix = 'r' + str(r['iteration'])
        if 'parsed' in r:
            result.update({prefix + '_' + k: v for k, v in r['parsed'].items()})
            result[prefix + '_equivalence'] = r['verdict'].get('logical_equivalence_confirmed')
            result[prefix + '_format_check'] = r['verdict'].get('format_check', '')
            result[prefix + '_feedback'] = r['verdict'].get('feedback', '')
    last = rounds[-1]
    if last.get('judge_attempts'):
        result['final_judge_think_trace'] = last['judge_attempts'][-1].get('reasoning', '')
    return result

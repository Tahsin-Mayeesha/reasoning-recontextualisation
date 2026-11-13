"""Resolve presets and model-independent Ollama CLI overrides."""
from copy import deepcopy


def thinking(value):
    value = value.strip()
    if value.lower() in ('auto', 'default', 'null'):
        return None
    if value.lower() in ('true', 'on'):
        return True
    if value.lower() in ('false', 'off'):
        return False
    if not value or value.lstrip('-').isdigit():
        raise ValueError('Thinking must be auto, true, false, or a model-supported named level')
    return value


def add_model_arguments(parser, stage):
    primary_flag = '--generator-model' if stage == 'adapt' else '--model'
    parser.add_argument(primary_flag, dest='primary_model', help='Any Ollama chat model tag; replaces the primary role preset')
    if stage == 'adapt':
        parser.add_argument('--judge-model', help='Independent Ollama judge model tag')
    for prefix in ('', 'judge-') if stage == 'adapt' else ('',):
        parser.add_argument('--' + prefix + 'base-url', help='Ollama server root URL, e.g. http://localhost:11434')
        parser.add_argument('--' + prefix + 'think', help='auto (model default), true, false, or a model-supported named level')
        parser.add_argument('--' + prefix + 'max-tokens', type=int)
        parser.add_argument('--' + prefix + 'num-ctx', type=int)
        parser.add_argument('--' + prefix + 'temperature', type=float)
        parser.add_argument('--' + prefix + 'timeout', type=float)


def resolve_config(config, args):
    config = deepcopy(config)
    stage = args.command
    if stage == 'solve':
        primary = deepcopy(config.get('solver', config.get('generator', {})))
        primary.update(config.get('solve', {}).get(args.mode, {}))
    else:
        primary = deepcopy(config.get('generator', {}))
    for role, prefix, selected in [('generator', '', args.primary_model)] + (
            [('judge', 'judge_', args.judge_model)] if stage == 'adapt' else []):
        current = primary if role == 'generator' else deepcopy(config.get('judge', {}))
        # A new model must not inherit another model's thinking controls or cloud settings.
        if selected is not None:
            current = {'provider': 'ollama', 'model': selected}
        if not current.get('provider') or not str(current.get('model', '')).strip():
            flag = '--generator-model' if role == 'generator' and stage == 'adapt' else '--model' if role == 'generator' else '--judge-model'
            raise ValueError(f'Specify {flag} or provide its role in --config')
        for name in ('base_url', 'think', 'max_tokens', 'num_ctx', 'temperature', 'timeout'):
            value = getattr(args, prefix + name, None)
            if value is None:
                continue
            if current['provider'] != 'ollama':
                raise ValueError(f'--{prefix.replace("_", "-") + name.replace("_", "-")} requires an Ollama role')
            current[name] = thinking(value) if name == 'think' else value
        for name in ('max_tokens', 'num_ctx', 'timeout'):
            if name in current and current[name] <= 0:
                raise ValueError(f'{role}.{name} must be positive')
        if 'temperature' in current and current['temperature'] < 0:
            raise ValueError(f'{role}.temperature cannot be negative')
        config[role] = current
    return config

"""Provider-specific transports. SDKs are loaded only for the selected provider."""
import json
import os
import time
import urllib.request
from dataclasses import dataclass


@dataclass
class Reply:
    text: str
    reasoning: str = ''
    finish_reason: str = ''


class Client:
    def __init__(self, config):
        self.config = dict(config)
        self.provider = self.config['provider']
        self.model = self.config['model']
        self.sdk = None
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError('A nonempty model tag is required')
        if self.config.get('retries', 3) < 1:
            raise ValueError('retries must be positive')

    def call(self, system, user):
        for attempt in range(self.config.get('retries', 3)):
            try:
                return self._call(system, user)
            except Exception:
                if attempt + 1 == self.config.get('retries', 3):
                    raise
                time.sleep(min(2 ** (attempt + 1), 30))

    def _call(self, system, user):
        c = self.config
        limit = c.get('max_tokens', 3000)
        messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}]
        if self.provider == 'ollama':
            # Native endpoint makes think a top-level parameter, not an options entry.
            options = dict(c.get('options', {}))
            options.update(num_predict=limit, num_ctx=c.get('num_ctx', 16384))
            body = {'model': self.model, 'messages': messages, 'stream': False, 'options': options}
            if 'keep_alive' in c:
                body['keep_alive'] = c['keep_alive']
            if c.get('temperature') is not None:
                body['options']['temperature'] = c['temperature']
            if c.get('think') is not None:
                body['think'] = c['think']
            request = urllib.request.Request(c.get('base_url', 'http://localhost:11434').rstrip('/') + '/api/chat',
                                             data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(request, timeout=c.get('timeout', 600)) as response:
                data = json.load(response)
            return Reply(data['message'].get('content', ''), data['message'].get('thinking', ''), data.get('done_reason', ''))
        if self.provider == 'openai':
            from openai import OpenAI
            if self.sdk is None:
                self.sdk = OpenAI(api_key=os.environ[c.get('api_key_env', 'OPENAI_API_KEY')], timeout=c.get('timeout', 600))
            if c.get('reasoning_effort'):
                response = self.sdk.responses.create(model=self.model, reasoning={'effort': c['reasoning_effort']},
                    max_output_tokens=limit, input=[{'role': 'developer', 'content': system}, messages[1]])
                return Reply(response.output_text, finish_reason=str(response.status))
            kwargs = {'model': self.model, 'messages': messages, 'max_tokens': limit}
            if c.get('temperature') is not None:
                kwargs['temperature'] = c['temperature']
            response = self.sdk.chat.completions.create(**kwargs)
            return Reply(response.choices[0].message.content or '', finish_reason=str(response.choices[0].finish_reason))
        if self.provider == 'anthropic':
            import anthropic
            if self.sdk is None:
                self.sdk = anthropic.Anthropic(api_key=os.environ[c.get('api_key_env', 'ANTHROPIC_API_KEY')], timeout=c.get('timeout', 600))
            kwargs = {'model': self.model, 'system': system, 'messages': [messages[1]], 'max_tokens': limit}
            if c.get('thinking_budget'):
                kwargs['thinking'] = {'type': 'enabled', 'budget_tokens': c['thinking_budget']}
                kwargs['max_tokens'] += c['thinking_budget']
            elif c.get('temperature') is not None:
                kwargs['temperature'] = c['temperature']
            response = self.sdk.messages.create(**kwargs)
            return Reply(''.join(b.text for b in response.content if b.type == 'text'),
                         ''.join(b.thinking for b in response.content if b.type == 'thinking'), str(response.stop_reason))
        if self.provider == 'gemini':
            from google import genai
            from google.genai import types
            if self.sdk is None:
                self.sdk = genai.Client(api_key=os.environ[c.get('api_key_env', 'GEMINI_API_KEY')])
            kwargs = {'system_instruction': system, 'max_output_tokens': limit}
            if c.get('temperature') is not None:
                kwargs['temperature'] = c['temperature']
            if c.get('include_thoughts') or 'thinking_budget' in c:
                thinking = {'include_thoughts': c.get('include_thoughts', False)}
                if 'thinking_budget' in c:
                    thinking['thinking_budget'] = c['thinking_budget']
                kwargs['thinking_config'] = types.ThinkingConfig(**thinking)
            response = self.sdk.models.generate_content(model=self.model, contents=user, config=types.GenerateContentConfig(**kwargs))
            if not response.candidates or not response.candidates[0].content:
                raise ValueError('Gemini returned no content')
            parts = response.candidates[0].content.parts or []
            return Reply(''.join(p.text or '' for p in parts if not getattr(p, 'thought', False)),
                         ''.join(p.text or '' for p in parts if getattr(p, 'thought', False)), str(response.candidates[0].finish_reason))
        raise ValueError(f'Unsupported provider: {self.provider}')

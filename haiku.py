#!/usr/bin/env python3

import requests

from dataclasses import dataclass
from random import choice
from typing import Any, Dict, List


def load_file(filename: str) -> List[str]:
    with open(filename) as f:
        return [line.strip() for line in f.readlines() if line.strip()]


adjectives = load_file('adjectives.txt')
nouns = load_file('nouns.txt')


@dataclass
class Word:
    text: str
    part_of_speech: str
    syllables: int


def random_noun() -> Word:
    noun = choice(nouns)
    params = {'sp': noun, 'md': 'ps'}
    resp = requests.get('https://api.datamuse.com/words', params=params)
    if not resp.ok:
        raise RuntimeError('uh oh')
    resp_json = resp.json()
    if not resp_json:
        raise RuntimeError('no results')
    matches = [
        word_from_result(result) for result in resp_json
        if 'n' in result.get('tags', []) and result['word'] == noun
    ]
    if not matches:
        raise RuntimeError(f'failed to find "{noun}"')
    return matches[0]


def random_haiku() -> str:
    return '\n'.join([
        random_line(5),
        random_line(7),
        random_line(5)
    ])


def random_line(syllables: int) -> str:
    noun = random_noun()
    while noun.syllables > syllables:
        noun = random_noun()
    adjs = []
    available_syllables = syllables - noun.syllables
    if available_syllables:
        candidates = get_related_adjectives(noun)
        for candidate in candidates:
            if candidate.syllables <= available_syllables:
                adjs.append(candidate)
                available_syllables -= candidate.syllables
                if not available_syllables:
                    break
    line = adjs + [noun]
    return ' '.join(word.text for word in line)


def get_related_adjectives(noun: Word) -> List[Word]:
    params = {'rel_jjb': noun.text, 'md': 'ps'}
    resp = requests.get('https://api.datamuse.com/words', params=params)
    if not resp.ok:
        raise RuntimeError('uh oh')
    resp_json = resp.json()
    if not resp_json:
        raise RuntimeError('no results')
    return [
        word_from_result(result) for result in resp_json if 'adj' in result.get('tags', [])
    ]


def get_related_nouns(adjective: Word) -> List[Word]:
    params = {'rel_jja': adjective.text, 'md': 'ps'}
    resp = requests.get('https://api.datamuse.com/words', params=params)
    if not resp.ok:
        raise RuntimeError('uh oh')
    resp_json = resp.json()
    if not resp_json:
        raise RuntimeError('no results')
    return [
        word_from_result(result) for result in resp_json if 'n' in result.get('tags', [])
    ]


def word_from_result(result: Dict[str, Any]) -> Word:
    return Word(
        text=result['word'],
        part_of_speech=get_part_of_speech(result.get('tags', [])),
        syllables=result['numSyllables']
    )


def get_part_of_speech(tags: List[str]) -> str:
    if not tags:
        return 'unknown'
    tag = tags[0]
    if tag == 'n':
        return 'noun'
    if tag == 'adj':
        return 'adjective'
    return 'unknown'

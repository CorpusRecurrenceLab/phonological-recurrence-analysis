"""Deterministic source adapter for the seven selected Biblical books.

The adapter resolves only the source-specific qere/ketiv and structural markup documented
in the frozen Sefaria verse inputs. It is imported by the public preparation workflow and tests;
it is not a general Hebrew critical-edition parser.
"""
import re

# Capture a whole consecutive bracket group; a ketiv may contain multiple words.
GROUP = re.compile(r'\[[^\[\]]+\](?:\s*\[[^\[\]]+\])*')
KETIV = re.compile(r'(?<![א-ת\u0591-\u05bd\u05bf\u05c1\u05c2\u05c4\u05c5\u05c7])([א-ת]+(?:[\s־]+[א-ת]+)*־?\s*)$')
MARK = re.compile(r'\(([פס׆])\)')


def adapt(source_text):
    """Return deterministic reading text, recorded edits, and unchanged source spans."""
    edits = []
    cursor = 0
    for match in GROUP.finditer(source_text):
        before = source_text[cursor:match.start()]
        ketiv_match = KETIV.search(before)
        start = cursor + ketiv_match.start() if ketiv_match else match.start()
        qere = ' '.join(re.findall(r'\[([^\[\]]+)\]', match.group()))
        edits.append({
            'kind': 'qere',
            'start': start,
            'end': match.end(),
            'original': source_text[start:match.end()],
            'ketiv': source_text[start:match.start()].strip(),
            'replacement': qere,
        })
        cursor = match.end()

    for match in MARK.finditer(source_text):
        edits.append({
            'kind': 'section' if match[1] in 'פס' else 'inverted_nun',
            'start': match.start(),
            'end': match.end(),
            'original': match.group(),
            'replacement': '',
            'marker': match[1],
        })

    edits.sort(key=lambda edit: edit['start'])
    output = []
    spans = []
    source_end = 0
    reading_pos = 0
    for edit in edits:
        if edit['start'] < source_end:
            raise ValueError('Overlapping source annotations')
        chunk = source_text[source_end:edit['start']]
        output.append(chunk)
        spans.append({
            'source_start': source_end,
            'source_end': edit['start'],
            'reading_start': reading_pos,
            'reading_end': reading_pos + len(chunk),
            'kind': 'unchanged',
        })
        reading_pos += len(chunk)
        edit['reading_start'] = reading_pos
        output.append(edit['replacement'])
        reading_pos += len(edit['replacement'])
        edit['reading_end'] = reading_pos
        source_end = edit['end']

    tail = source_text[source_end:]
    output.append(tail)
    spans.append({
        'source_start': source_end,
        'source_end': len(source_text),
        'reading_start': reading_pos,
        'reading_end': reading_pos + len(tail),
        'kind': 'unchanged',
    })
    reading = ''.join(output)

    if re.search(r'[\[\]()<>]', reading):
        raise ValueError('Unrecognized source annotation')

    # Reconstruct the source to verify that the recorded edits are reversible.
    restored = reading
    for edit in reversed(edits):
        restored = (
            restored[:edit['reading_start']]
            + edit['original']
            + restored[edit['reading_end']:]
        )
    if restored != source_text:
        raise ValueError('Source reconstruction failed')

    return reading, edits, spans

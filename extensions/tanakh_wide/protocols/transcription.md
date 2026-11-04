# Computational transcription protocol

The analysis uses a deterministic segmental encoding, not a diplomatic transcription and not a reconstruction of historical Tiberian pronunciation. The executable implementation in `src/core/phonetic_core_v2.py` is authoritative.

## Vowels

The five vowel units are `a`, `e`, `i`, `o`, and `u`.

- patah -> `a`
- ordinary qamats (U+05B8) -> `a`
- explicit qamats qatan (U+05C7) -> `o`
- segol and tsere -> `e`
- hiriq -> `i`
- holam -> `o`
- qubbuts/shuruq -> `u`
- reduced vowels follow their corresponding quality
- word-initial sheva is represented by the fixed executable rule; internal/final sheva normally adds no vowel
- furtive patah is reordered before the final guttural

## Consonants

Begadkefat distinctions are retained for bet/kaf/pe (`b/v`, `k/kh`, `p/f`). `sh`, `kh`, and `ts` are atomic units. Shin/sin are `sh/s`; tsadi is `ts`; qof is `q`; tet and tav are both `t`; het is `h`. Aleph and ayin add no independent consonantal unit in this profile. Final he without its own vowel/dagesh is omitted. Divine-name and perpetual-qere forms have explicit executable rules.

These choices intentionally simplify several historical and modern distinctions. Exact computational identity therefore does not imply identity in every Hebrew pronunciation tradition.

## Expanded correspondence mode

The expanded mode permits **one** direct consonant substitution per mixed triplet from the fixed symmetric set:

`f~v`, `p~b`, `d~t`, `b~v`, `z~s`, `h~kh`, `q~k`.

No vowel substitution, transitive closure, reversal, or multiple substitution is allowed.

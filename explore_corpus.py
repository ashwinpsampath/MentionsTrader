"""See what we have in our Trump speech corpus."""
from collections import Counter
from src.corpus import load_corpus


corpus = load_corpus()
print(f"\nCorpus loaded: {len(corpus)} speeches\n")

# Per-speech summary
print("=== Per speech ===")
total_trump_chars = 0
for speech in corpus:
    trump_text = speech.text_by("Trump")
    other_speakers = set(t.speaker for t in speech.turns) - {"Trump"}
    
    print(f"  {speech.date}  {speech.event_type:13s}  "
          f"Trump: {len(trump_text):>7,} chars  "
          f"others: {len(other_speakers)}  "
          f"({speech.title[:50]})")
    total_trump_chars += len(trump_text)

print(f"\nTotal Trump speech text across corpus: {total_trump_chars:,} characters")
print(f"Approx. words (chars/5): {total_trump_chars // 5:,}")

# Speaker distribution across the entire corpus
print("\n=== All speakers across corpus ===")
all_speakers = Counter()
for speech in corpus:
    for turn in speech.turns:
        all_speakers[turn.speaker] += 1

for speaker, count in all_speakers.most_common(20):
    print(f"  {speaker}: {count} turns")
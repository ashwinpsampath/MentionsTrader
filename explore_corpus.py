from src.corpus import load_corpus

corpus = load_corpus()
print(f"Loaded {len(corpus)} calls\n")
for s in corpus:
    print(f"  {s.date}  {s.ticker}  {len(s.turns)} turns, "
          f"{len(s.text_by_company()):,} company chars  ({s.title})")
    print(s.company_representatives)

for turn in corpus[1].turns:
        print(turn)
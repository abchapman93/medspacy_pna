def disambiguate_cap(matcher, doc, i, matches):
    (_, start, end) = matches[i]
    span = doc[start:end]
    if span._.window(n=5)._.contains(r"mg", case_insensitive=True):
        matches.pop(i)
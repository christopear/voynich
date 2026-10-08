"""Post-search checks of the synthetic encoder's declared unitization rule."""


def audit_greedy_unitization(plaintext, emitted_units, allowed_units):
    """Check whether a decoded path could follow longest-match unit selection.

    No key search or fitting occurs. This checks unitization only, not key
    completeness, homophone allocation, random choices or historical use.
    """
    if ''.join(emitted_units)!=plaintext:
        raise ValueError('path emissions do not reproduce the decoded text')
    if any(not unit or ' ' in unit for unit in allowed_units):
        raise ValueError('preserved-space emissions must be nonempty nonspace units')
    units=sorted(set(allowed_units),key=lambda u:(-len(u),u))
    selected=[];position=0
    while position<len(plaintext):
        if plaintext[position]==' ':
            selected.append(' ');position+=1;continue
        options=[unit for unit in units if plaintext.startswith(unit,position) and
            (len(unit)<=2 or ((position==0 or plaintext[position-1]==' ') and
                (position+len(unit)==len(plaintext) or plaintext[position+len(unit)]==' ')))]
        if not options:raise ValueError('decoded text cannot be encoded by this inventory')
        selected.append(options[0]);position+=len(options[0])
    return {'matches':list(emitted_units)==selected,'canonical_unit_count':len(selected),
            'decoded_path_unit_count':len(emitted_units),
            'scope':'Greedy unit selection only; post-search diagnostic, original gates unchanged.'}

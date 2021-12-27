def same_trait_name(collection):
    for group in collection:
        if 'traits' in group:
            for trait in group['traits']:
                for other_group in collection:
                    if 'traits' in other_group:
                        for other_trait in other_group['traits']:
                            if other_group['group'] != group['group'] and 'traits' in other_group and trait['title'] == other_trait['title']:
                                print("Notice: traits '%s.%s' and '%s.%s' have same names" % (group['group'], trait['title'], other_group['group'], other_trait['title']))

def trait_names(collection):
    names = []
    for group in collection:
        if 'traits' in group:
            for trait in group['traits']:
                names.append({'group': group['group'], 'name': trait['title']})
    return names

def adapted_for_unknown(collection):
    for group in collection:
        if 'traits' in group:
            traits = group['traits']
            for trait in traits:
                if 'adapted-to' in trait:
                    for a in trait['adapted-to']:
                        if not any(n['name'] == a for n in trait_names(collection)):
                            print("Notice: '%s.%s' adapted to none existed trait name '%s'" % (group['group'], trait['title'], a))

def excluded_for_unknown(collection):
    for group in collection:
        if 'traits' in group:
            traits = group['traits']
            prev_name = ''
            for trait in traits:
                if trait['title'] == prev_name:
                    continue
                else:
                    prev_name = trait['title']
                if 'exclude' in trait:
                    for e in trait['exclude']:
                        if not any(n['name'] == e for n in trait_names(collection)):
                            print("Notice: '%s.%s' excluded for none existed trait name '%s'" % (group['group'], trait['title'], e))

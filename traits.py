import os
import json

def is_real_file(file):
    if os.path.isfile(file):
        return True
    else:
        print("Warning: file %s is not a real path (this trait skipped)" % file)
        return False

def load(input_file):
    """
    Load traits json file and return list of groups like:
    [
        {
            group: 'head',
            traits: [
                {
                    title: 'Head 1',
                    file: ['/1.png', '2.png'],
                    condition: ['Body1'],
                    excluded: ['Leg 3']
                }
            ],
            current: {}
        },
        ...
    ]
    Where current represent traits[0] by default
    """
    groups = []
    with open(input_file) as json_file:
        try:
            parsed = json.load(json_file)
            for group_name,traits in parsed.items():
                group = {"group": group_name, "traits": []}
                for trait_name, trait in traits.items():
                    file = trait['file']
                    paths = []
                    #single file as string
                    if isinstance(file, str) and is_real_file(file) == True: 
                        paths.append({'title': trait_name, 'file': [file]})
                    #more then 1 file in array style of strings
                    elif isinstance(file, list) and all(isinstance(f, str) and is_real_file(f) for f in file): 
                        paths.append({'title': trait_name, 'file': file})
                    #single file in dict style with path as string without condition
                    elif isinstance(file, dict) and 'path' in file and isinstance(file['path'], str) and 'adapted-to' not in file: 
                        paths.append({'title': trait_name, 'file': [file['path']]})
                    #single file in dict style with path as array of strings without condition
                    elif isinstance(file, dict) and 'path' in file and isinstance(file['path'], list) and all(isinstance(f, str) and is_real_file(f) for f in file['path']) and 'adapted-to' not in file:
                        paths.append({'title': trait_name, 'file': file['path']})
                    #single file in dict style with path as string with condition
                    elif isinstance(file, dict) and 'path' in file and isinstance(file['path'],str) and 'adapted-to' in file:
                        paths.append({'title': trait_name, 'file': [file['path']], 'adapted-to': file['adapted-to']})
                    #single file in dict style with path as array of strings with condition
                    elif isinstance(file, dict) and 'path' in file and isinstance(file['path'],list) and 'adapted-to' in file:
                        paths.append({'title': trait_name, 'file': file['path'], 'adapted-to': file['adapted-to']})
                    elif isinstance(file, list):
                        has_default = False
                        for t_file in file:
                            if isinstance(t_file, str) and is_real_file(t_file):
                                if has_default == False:
                                    paths.append({'title': trait_name, 'file': [t_file]})
                                    has_default = True
                                else:
                                    print('Warning: more then 1 default path for trait %s, %s ignored' % (trait_name,t_file))
                            if isinstance(t_file, list) and all(isinstance(f, str) and is_real_file(f) for f in t_file):
                                if has_default == False:
                                    paths.append({'title': trait_name, 'file': t_file})
                                    has_default = True
                                else:
                                    print('Warning: more then 1 default path for trait %s, %s ignored' % (trait_name,str(t_file)))
                            if isinstance(t_file, dict) and 'path' in t_file:
                                if isinstance(t_file['path'], str):
                                    if 'adapted-to' in t_file:
                                        paths.append({'title': trait_name, 'file': [t_file['path']], 'adapted-to':t_file['adapted-to']})
                                    elif has_default == False:
                                        paths.append({'title': trait_name, 'file': [t_file['path']]})
                                        has_default = True
                                elif isinstance(t_file['path'], list):
                                    if 'adapted-to' in t_file:
                                        paths.append({'title': trait_name, 'file': t_file['path'], 'adapted-to':t_file['adapted-to']})
                                    elif has_default == False:
                                        paths.append({'title': trait_name, 'file': t_file['path']})
                                        has_default = True
                    for path in paths:
                        if 'excluded' in trait and isinstance(trait['excluded'], str):
                            path['excluded'] = [trait['excluded']]
                        elif 'excluded' in trait and isinstance(trait['excluded'], list):
                            path['excluded'] = trait['excluded']
                        group['traits'].append(path)
                        if 'current' not in group:
                            group['current'] = path
                groups.append(group)
            return groups
        except Exception as exception:
            print('Error in parsing layers from traits file (%s)' % input_file)
            print(exception)

def check_condition(condition, groups):
    for trait in groups:
        for c in condition:
            if c == trait['current']['title']:
                return True
    return False

def check_exclude(exclude, groups):
    for trait in groups:
        for c in exclude:
            if c == trait['current']['title']:
                return True
    return False
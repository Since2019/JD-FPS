import unreal as u
def texture(entry):
    name='Bolt762' if entry['name']=='7.62 栓动步枪' else 'HK416' if entry['name']=='HK416' else 'Weapon' if entry['kind']=='WEAPON' else 'Helmet' if entry['name']=='FAST 风格头盔' else None
    return u.load_asset('/Game/Factory/Visual4/UI/Photo_'+name) if name else None

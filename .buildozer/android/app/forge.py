def subclasses(mother_class):
    output = {}
    for tmp in mother_class.__subclasses__():
        output[tmp.__name__] = tmp
        output.update(subclasses(tmp))
    return output

def forge_function(mother_class, config, config_type=None):
    if config_type is None:
        config_type = config.get('type')
        config = config.get('config')
    tmp = mother_class.subclasses.get(config_type)
    if tmp is None:
        mother_class.subclasses = subclasses(mother_class)
        tmp = mother_class.subclasses.get(config_type)
    if tmp:
        return tmp(**config)
    return None
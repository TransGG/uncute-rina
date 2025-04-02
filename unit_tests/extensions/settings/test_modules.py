from extensions.settings.objects import EnabledModules, ModuleKeys


def test_matching_keys():
    # Arrange
    em = EnabledModules.__annotations__.keys()
    emk = set(i for i in dir(ModuleKeys) if not i.startswith("_"))

    # Assert
    assert set(em) == emk
    # for assurance
    assert sorted(set(em)) == sorted(em)


def test_module_key_attribute_match_value():
    module_keys = [i for i in dir(ModuleKeys) if not i.startswith("_")]
    incorrect_keys = []

    for module_key in module_keys:
        if getattr(ModuleKeys, module_key) != module_key:
            incorrect_keys.append(module_key)

    assert incorrect_keys == []

import json


def translate_personal(id_file_path, input, from_lang="zh-cn", to_lang="en"):
    if not id_file_path:
        raise ValueError("Have to set --id-file-path")
    f = open(id_file_path)
    personal_dict = json.load(f)
    if from_lang == "zh-cn":
        for chinese, english in personal_dict.items():
            output = input.replace(chinese, english)
    elif from_lang == "en":
        en_cn = dict([(value, key) for key, value in personal_dict.items()])
        for english, chinese in en_cn.items():
            output = input.replace(english, chinese)
    return output
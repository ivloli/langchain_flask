# helper.py
import os
import json
def is_list_of_dicts_with_str_keys_and_values(obj):
    if not isinstance(obj, list):
        return False

    for item in obj:
        if not isinstance(item, dict):
            return False
        for key, value in item.items():
            if not (isinstance(key, str) and isinstance(value, str)):
                return False
    
    return True

def list_csv_files_in_current_directory():
    current_directory = os.getcwd()
    csv_files = [file for file in os.listdir(current_directory) if file.endswith('.csv')]
    return csv_files

def list_csv_files_in_sub_directory(sub_path: str):
    current_directory = os.getcwd()
    sub_directory = os.path.join(current_directory, sub_path)
    if file_exists(sub_directory):
        csv_files = [file for file in os.listdir(sub_directory) if file.endswith('.csv')]
        return csv_files
    else:
        return list[str]([])

def file_exists(file_path):
    return os.path.exists(file_path)

def get_common_keys(list_of_dicts):
    if not list_of_dicts:
        return set()  # Return an empty set if the list is empty

    common_keys = set(list_of_dicts[0].keys())  # Initialize with the keys of the first dictionary

    for dictionary in list_of_dicts[1:]:
        common_keys.intersection_update(dictionary.keys())

    return list(common_keys)

def all_elements_in_list_a(a, b):
    # convert list to set
    set_a = set(a)
    set_b = set(b)

    return set_b.issubset(set_a)

def parse_json(json_str):
    try:
        data = json.loads(json_str)
        return data, None  # 返回解析后的数据和错误信息为None
    except json.JSONDecodeError as e:
        error_msg = {"error": "JSON解析错误", "message": str(e)}
        return None, error_msg  # 返回None和错误信息字典

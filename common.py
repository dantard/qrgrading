import os

def get_workspace_paths(base):
    dir_workspace = base + os.sep
    dir_data = dir_workspace + "data" + os.sep
    dir_scanned = dir_workspace  + "scanned" + os.sep
    dir_generated = dir_workspace + "generated" + os.sep
    dir_xls = dir_workspace + "results" + os.sep + "xls" + os.sep
    dir_publish = dir_workspace + "results" + os.sep + "pdf" + os.sep
    return dir_workspace, dir_data, dir_scanned, dir_generated, dir_xls, dir_publish


def get_temp_paths(base):
    dir_pool = base + os.sep + "pool" + os.sep
    dir_images = dir_pool + os.sep + "images" + os.sep
    return dir_pool, dir_images

def check_workspace():
    current_dir = os.getcwd()
    dir_name = os.path.basename(current_dir)
    name = dir_name.split("-")
    if len(name) != 2 or name[0] != "qrgrading" or len(name[1]) != 8 or not name[1].isdigit():
        return False
    return True

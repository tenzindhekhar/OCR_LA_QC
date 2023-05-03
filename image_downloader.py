import os
import json
import shutil
import requests
from tqdm import tqdm
from glob import glob
from pathlib import Path
from generate_pagexml import build_xml_file


def create_dir(dir_name: str) -> None:
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def read_jsonl(jsonl_file: str) -> list[str]:
    f = open(jsonl_file, "r")
    json_info = f.readlines()
    return json_info


def filter_missing_annotations(json_records: list[str]) -> tuple[list[str], list[str]]:
    valid_annotations = []
    missing_annotations = []

    for json_rec in json_records:
        if "span" in json_rec:
            valid_annotations.append(json_rec)
        else:
            missing_annotations.append(json_rec)

    return valid_annotations, missing_annotations


def remove_duplicates(json_records: list[str]) -> tuple[list[str], list[str]]:
    img_names = []
    valid_records = []
    duplicates = []

    for json_rec in json_records:
        json_info = json.loads(json_rec)
        image_name = json_info["id"].split(".")[0]

        if image_name not in img_names:
            valid_records.append(json_info)
        else:
            duplicates.append(json_info)

    return valid_records, duplicates


def download_image(json_record, out_dir) -> None:
    image_name = json_record["id"].split(".")[0]
    url = json_record["image"]

    res = requests.get(url, stream=True)
    out_file = f"{out_dir}/{image_name}.jpg"

    if not os.path.isfile(out_file):
        if res.status_code == 200:
            out_file = f"{out_dir}/{image_name}.jpg"

            with open(out_file, "wb") as f:
                shutil.copyfileobj(res.raw, f)


def get_images(json_file: str, generate_xml: bool = True) -> tuple[list, list]:
    out_dir_name = os.path.basename(json_file).split(".")[0]
    img_out_dir = os.path.join(dataset_path, out_dir_name)

    create_dir(img_out_dir)

    json_info = read_jsonl(json_file)
    valid_annotations, missing_anotations = filter_missing_annotations(json_info)
    json_records, duplicates = remove_duplicates(valid_annotations)

    failed_downloads = []

    print(f"Processing: {out_dir_name}, downloading {len(json_records)} Images...")
    for idx in tqdm(range(len(json_records))):
        try:
            download_image(json_records[idx], img_out_dir)
        except:
            failed_downloads.append(json_records["image"])
            print(f"Error downloading image: {json_records[idx]['id']}")

    # insert building xml file here
    if generate_xml:
        xml_out = os.path.join(img_out_dir, "page")
        create_dir(xml_out)

        for json_record in json_records:
            build_xml_file(json_record, xml_out)

    return failed_downloads, duplicates, missing_anotations


def write_log(
    json_file: str, failed_dls: list, duplicates: list, missing_annotations: str
) -> None:
    json_fname = os.path.basename(json_file).split(".")[0]
    log_out = f"{dataset_path}/log_{json_fname}.txt"

    with open(log_out, "w") as f:
        f.write(f"---- {json_fname} ---- \n")
        f.write(f"#### Missing Annotations ####\n")

        for missing_annot in missing_annotations:
            f.write(f"{missing_annot}\n")

        f.write(f"#### Failed Downloads ####\n")

        for failed_dl in failed_dls:
            f.write(f"{failed_dl}\n")

        f.write(f"#### Duplicte Entry ####\n")

        for dupl in duplicates:
            f.write(f"{dupl}\n")


if __name__ == "__main__":
    # change this path as needed
    dataset_path = "2023-04-21-07-04-09"
    json_files = glob(f"{dataset_path}/*.jsonl")

    for json_f in json_files:
        failed_dls, duplicates, missing_anotations = get_images(json_f)
        write_log(json_f, failed_dls, duplicates, missing_anotations)

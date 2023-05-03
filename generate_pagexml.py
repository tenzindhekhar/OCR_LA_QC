import os
import json
from glob import glob
from tqdm import tqdm
from xml.dom import minidom
from typing import List, Tuple
# from natsort import natsorted
import xml.etree.ElementTree as etree


def read_jsonl(jsonl_file: str) -> List[str]:
    f = open(jsonl_file, "r")
    json_info = f.readlines()

    return json_info


def get_image_name(x: str) -> str:
    return os.path.basename(x).split(".")[0]


def get_json_image_name(x: str) -> str:
    return x["id"].split(".")[0]


def get_json_coordinates(contour):
    points = ""

    for box in contour:
        point = f"{box[0]},{box[1]} "
        points += point
    return points


def build_xml_file(json_record: str, xml_out: str) -> None:

    n_spans = len(json_record["spans"])
    url = json_record["image"]
    image_name = os.path.basename(url).split("?")[0].split(".")[0]
    xml_out_file = f"{xml_out}/{image_name}.xml"

    if not os.path.isfile(xml_out_file):
        root = etree.Element("PcGts")
        root.attrib[
            "xmlns"
        ] = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"
        root.attrib["xmlns:xsi"] = "http://www.w3.org/2001/XMLSchema-instance"
        root.attrib[
            "xsi:schemaLocation"
        ] = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15 http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15/pagecontent.xsd"

        url = json_record["image"]
        metadata = etree.SubElement(root, "Metadata")
        creator = etree.SubElement(metadata, "Creator")
        creator.text = "Transkribus"
        created = etree.SubElement(metadata, "Created")
        created.text = "2022-09-06T12:00:26.622+02:00"
        last_change = etree.SubElement(metadata, "LastChanged")
        last_change.text = "2022-09-06T12:02:29.072+02:00"

        page = etree.SubElement(root, "Page")
        page.attrib["imageFilename"] = image_name
        img_width = json_record["width"]
        img_height = json_record["height"]
        page.attrib["imageWidth"] = f"{img_width}"
        page.attrib["imageHeight"] = f"{img_height}"

        reading_order = etree.SubElement(page, "ReadingOrder")
        ordered_group = etree.SubElement(reading_order, "OrderedGroup")
        ordered_group.attrib["id"] = f"1234_{0}"
        ordered_group.attrib["caption"] = "Regions reading order"

        region_ref_indexed = etree.SubElement(reading_order, "RegionRefIndexed")
        region_ref_indexed.attrib["index"] = "0"
        region_ref = "region_main"
        region_ref_indexed.attrib["regionRef"] = region_ref

        for i in range(n_spans):
            label = json_record["spans"][i]["label"]

            if label == "Text-Area":
                text_region = etree.SubElement(page, "TextRegion")
                text_region.attrib["id"] = region_ref
                text_region.attrib["custom"] = "readingOrder {index:0;}"

                text_region_coords = etree.SubElement(text_region, "Coords")
                text_region_coords.attrib["points"] = get_json_coordinates(
                    json_record["spans"][i]["points"]
                )

            elif label == "Margin":
                text_region = etree.SubElement(page, "TextRegion")
                text_region.attrib["id"] = region_ref
                text_region.attrib[
                    "custom"
                ] = "readingOrder {index:0;} structure {type:marginalia;}"

                text_region_coords = etree.SubElement(text_region, "Coords")
                text_region_coords.attrib["points"] = get_json_coordinates(
                    json_record["spans"][i]["points"]
                )

            elif label == "Caption":
                text_region = etree.SubElement(page, "TextRegion")
                text_region.attrib["id"] = region_ref
                text_region.attrib[
                    "custom"
                ] = "readingOrder {index:0;} structure {type:caption;}"

                text_region_coords = etree.SubElement(text_region, "Coords")
                text_region_coords.attrib["points"] = get_json_coordinates(
                    json_record["spans"][i]["points"]
                )

            elif label == "Illustration":
                image_region = etree.SubElement(page, "ImageRegion")
                image_region.attrib["custom"] = "readingOrder {index:1;}"
                image_region_coords = etree.SubElement(image_region, "Coords")
                image_region_coords.attrib["points"] = get_json_coordinates(
                    json_record["spans"][i]["points"]
                )

            xmlparse = minidom.parseString(etree.tostring(root))
            prettyxml = xmlparse.toprettyxml()

            with open(xml_out_file, "w", encoding="utf-8") as f:
                f.write(prettyxml)


def generate_pagexml(json_file: str) -> List[str]:
    json_file_n = os.path.basename(json_file).split(".")[0]
    json_records = read_jsonl(json_file)

    image_path = os.path.join(dataset_path, json_file_n)
    images = glob(f"{image_path}/*.jpg")
    image_names = [get_image_name(x) for x in images]

    xml_out = os.path.join(image_path, "page")

    if not os.path.exists(xml_out):
        os.makedirs(xml_out)

    skipped_entries = []

    for json_record in json_records:
        json_info = json.loads(json_record)
        json_img_name = get_json_image_name(json_info)

        if json_img_name in image_names:
            build_xml_file(json_info, xml_out)
        else:
            skipped_entries.append(json_record)

    return skipped_entries


if __name__ == "__main__":
    # change this path as needed
    dataset_path = "2023-04-21-07-04-09"
    json_files = glob(f"{dataset_path}/*.jsonl")

    for json_f in json_files:
        json_f_name = os.path.basename(json_f).split(".")[0]
        skipped_entries = generate_pagexml(json_f)

        log_out = f"{dataset_path}/{json_f_name}_xml_log.txt"

        with open(log_out, "w") as f:
            for entry in skipped_entries:
                f.write(
                    f"The following entries were skipped during PageXML generation:\n"
                )
                f.write(f"{entry}\n")

# import the necessary packages
from PIL import Image, ImageOps
import pytesseract
from pytesseract import Output
import argparse
import cv2
import os
import json

def process_list(text: str) -> dict:
    final = {}
    items = text.split("\n")[4:][:-1]

    for item in items:
        if item == "":
            continue
        x = item.split(" ")
        itemtype = x[1].lower()
        if itemtype not in final:
            final[itemtype] = {}
        final[itemtype][x[0]] = {}
    return final

def process_query(text: str, existing: dict) -> dict:
    current = ("", "")
    lines = text.split("\n")
    for line in lines:
        if line != "":
            stuff = line.split(": ")
            if stuff[0] == "ID":
                for cat in existing:
                    for item in existing[cat]:
                        if item == stuff[1]:
                            current = (cat, stuff[1])
                            break
            if stuff[0] == "LOCATION":
                cat, id = current
                if cat == "" or id == "":
                    continue
                if id not in existing[cat]:
                    print("warning - item found in query, not in list", id)
                existing[cat][id]["location"] = stuff[1]

    return existing

def print_results(items: dict):
    for category in items:
        print(category.upper())
        for item in items[category]:
            print("  ├──" + item)
            for prop in items[category][item]:
                print("    ├── {}: {}".format(prop.upper(), items[category][item][prop]))

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("image",
	help="path to input image to be OCR'd")
ap.add_argument("-t", "--type", default="list")
ap.add_argument("-d", "--debug", dest="debug", action="store_true",
    help="whether to save results of ocr to file")
ap.add_argument("-p", "--pretty-print", dest="prettyprint", action="store_true",
    help="whether to print nice data, or produce json")

ap.set_defaults(debug=False, prettyprint=False)
args = vars(ap.parse_args())

# load the example image and convert it to grayscale
image = cv2.imread(args["image"])
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
filename = "{}.png".format(os.getpid())
cv2.imwrite(filename, gray)

# load the image as a PIL/Pillow image and apply some basic transformations.
img = Image.open(filename)
os.remove(filename)
img = img.crop((300, 120, 2000, 1300))
img = ImageOps.invert(img)

res = {}
if args["type"] == "list":
    res = process_list(pytesseract.image_to_string(img))
    f = open("list.json", "w+")
    f.write(json.dumps(res))
    f.close()

if args["type"] == "query":
    f = open("list.json", "r")
    existing = json.loads(f.read())
    res = process_query(pytesseract.image_to_string(img), existing)

if args["prettyprint"]:
    print_results(res)
else:
    print(json.dumps(res, indent=2))

if args["debug"]:
    img.save(filename)
    img = cv2.imread(filename)
    os.remove(filename)

    d = pytesseract.image_to_data(img, output_type=Output.DICT)
    n_boxes = len(d['level'])
    for i in range(n_boxes):
        (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 1)

    cv2.imwrite("f.png", img)
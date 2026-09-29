from PIL import Image, ImageDraw, ImageFont
import shopify
from datetime import datetime, timedelta
import base64
from django.conf import settings
import os

font_size = 96.4999

# Frontend posts Fonts[i].name from the theme customizer (see niko Assets.js).
# Folder names are ASCII-safe; "München" maps to Munchen/Munchen.otf.
FONT_FILES = {
    "Aachen": ("Aachen", "Aachen.ttf"),
    "Berlin": ("Berlin", "Berlin.otf"),
    "Bremen": ("Bremen", "Bremen.otf"),
    "Dortmund": ("Dortmund", "Dortmund.otf"),
    "Frankfurt": ("Frankfurt", "Frankfurt.otf"),
    "Hamburg": ("Hamburg", "Hamburg.otf"),
    "Hannover": ("Hannover", "Hannover.otf"),
    "Kiel": ("Kiel", "Kiel.ttf"),
    "Koeln": ("Koeln", "Koeln.otf"),
    "Leipzig": ("Leipzig", "Leipzig.otf"),
    "Mainz": ("Mainz", "Mainz.otf"),
    "Osnabrueck": ("Osnabrueck", "Osnabrueck.otf"),
    "Potsdam": ("Potsdam", "Potsdam.otf"),
    "Regensburg": ("Regensburg", "Regensburg.otf"),
    "Stuttgart": ("Stuttgart", "Stuttgart.otf"),
    "Bonn": ("Bonn", "Bonn.otf"),
    "Duisburg": ("Duisburg", "Duisburg.otf"),
    "Essen": ("Essen", "Essen.otf"),
    "Freiburg": ("Freiburg", "Freiburg.otf"),
    "Paderborn": ("Paderborn", "Paderborn.otf"),
    "Wuppertal": ("Wuppertal", "Wuppertal.otf"),
    "München": ("Munchen", "Munchen.otf"),
    "Munchen": ("Munchen", "Munchen.otf"),
}

# Reuse one draw context for bbox measurement (image size does not clip textbbox).
_MEASURE_DRAW = ImageDraw.Draw(Image.new("RGB", (64, 64)))


def _text_bbox_size(text, font_path, font_size, letter_spacing=0):
    """Return (width, height) of ink bounding box at the given font size."""
    font = ImageFont.truetype(font_path, font_size)
    bbox = _MEASURE_DRAW.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0] + (max(len(text) - 1, 0) * letter_spacing)
    height = bbox[3] - bbox[1]
    return width, height


def calculate_text_size(text, font_path, font_size, letter_spacing=0):
    # Load the font
    font = ImageFont.truetype(font_path, font_size)
    
    # Create an image with enough size to draw the text
    image = Image.new('RGB', (1000, 1000))
    draw = ImageDraw.Draw(image)
    
    # Get the bounding box of the text
    bbox = draw.textbbox((0, 0), text, font=font)
    
    # Calculate width and height including letter spacing
    width = bbox[2] - bbox[0] + (len(text) - 1) * letter_spacing
    height = bbox[3] - bbox[1]
    
    # Scale width and height to float values
    width = width * (font_size / 100.0)  # Adjust the scaling factor as needed
    height = height * (font_size / 100.0)  # Adjust the scaling factor as needed
        
    return width, height

def calculate_text_width(text, font_path, desired_height, letter_spacing=0):
    """
    Find font size where ink height >= desired_height, return ink width.
    Same contract as before (units match views.get_measurements *10 scale).
    Uses binary search for speed; result matches the previous linear scan.
    """
    if desired_height is None or desired_height <= 0:
        return None

    min_font_size = 1
    max_font_size = 4000
    best_width = None

    low, high = min_font_size, max_font_size
    while low <= high:
        mid = (low + high) // 2
        width, height = _text_bbox_size(text, font_path, mid, letter_spacing)
        if height >= desired_height:
            best_width = width
            high = mid - 1
        else:
            low = mid + 1

    return best_width

def calculate_text_height(text, font_path, desired_width, letter_spacing=0):
    """
    Find font size where ink width >= desired_width, return ink height.
    Same contract as before; binary search for speed.
    """
    if desired_width is None or desired_width <= 0:
        return None

    min_font_size = 1
    max_font_size = 4000
    best_height = None

    low, high = min_font_size, max_font_size
    while low <= high:
        mid = (low + high) // 2
        width, height = _text_bbox_size(text, font_path, mid, letter_spacing)
        if width >= desired_width:
            best_height = height
            high = mid - 1
        else:
            low = mid + 1

    return best_height


def calculate_widths_for_heights(text, font_path, heights, letter_spacing=0):
    results = []
    for height in heights:
        width = calculate_text_width(text, font_path, height, letter_spacing)
        results.append({"height": height, "width": width})
    return results

def create_product(title,price,tag,image,weight=0.0,weight_unit='kg',requires_shipping=True):
    
    try:
        product = shopify.Product()
        product.title = title
        product.published = True
        product.status = 'active'
        product.tags = tag
        product.save()
        id = product.id

        # Add product to this collection while creating
        collection_id = 632313119050
        collect = shopify.Collect()
        collect.product_id = id
        collect.collection_id = collection_id
        collect.save()

        upload_product_image(id,image)
        image = None
        return createVariant(id,title,price,image,weight,weight_unit,requires_shipping)
    except Exception as e:
        print(e)
        return None

def createVariant(id,title,price,image,weight,weight_unit,requires_shipping):
    now = (datetime.now() + timedelta(hours=3)).strftime("%H:%M:%S_%d/%m/%Y")
    try:

        image_id = None
        print(price,type(price))
        product = shopify.Product.find(id)
        if image == None:
            if len(product.images) > 0:
                image_id = product.images[0].id if product.images[0] else None
        else:
            image_id = upload_product_image(product_id=id,file=image)
        v = shopify.Variant()
        v.option1 = title + ' - ' + now
        v.price = float(price)/100
        v.image_id = image_id
        v.weight = weight
        v.weight_unit = weight_unit
        v.requires_shipping = requires_shipping
        v.inventory_policy = 'continue'
        product.add_variant(v)
        return v.to_dict()
    except Exception as e:
        print("Create variant exception",e)
    return None

def upload_product_image(product_id,file):
    try:
        print('product id',product_id)
        image = shopify.Image({'product_id':product_id})
        image.position = 1
        image.src = file
        image.save()
        return image.id
    except Exception as e:
        print('Exception while upload image>>',e)
        return None
    
def get_font_path(font):
    """
    Resolve shop font display name -> font file on disk.
    Raises ValueError for unknown names (no silent Arial fallback).
    Raises FileNotFoundError if the mapped file is missing.
    """
    entry = FONT_FILES.get(font)
    if entry is None:
        raise ValueError(f"Unknown font: {font}")

    folder, filename = entry
    font_path = os.path.join(settings.BASE_DIR, "static", "fonts", folder, filename)
    if not os.path.isfile(font_path):
        raise FileNotFoundError(f"Font file missing: {font_path}")
    return font_path
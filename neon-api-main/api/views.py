from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime, timedelta
from shopify_app.decorators import session_token_required,session_token_required_api
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import os
import json
import base64

from .helpers import calculate_text_height,calculate_text_width,create_product,createVariant,get_font_path,calculate_widths_for_heights

import shopify

@session_token_required
def products(request):
    products = shopify.Product.find()

    return JsonResponse({'products': [p.to_dict() for p in products]})

@session_token_required
def orders(request):
    orders = shopify.Order.find(status='any')

    return JsonResponse({'orders': [o.to_dict() for o in orders]})

def get_drinks(request):
    return JsonResponse({"drinks": "drink data"})

@csrf_exempt
def get_measurements(request):
    if(request.method == 'POST'):
        try:
            font_path = get_font_path(request.POST.get('font','Aachen'))
        except (ValueError, FileNotFoundError) as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        print(font_path)
        font_size = 96.4999  # Use float for more precision
        text = request.POST.get('text','')
        letter_spacing = 0  # Adjust letter spacing here
        width = request.POST.get('width',None)
        height = request.POST.get('height',None)
        # print (f"{width} - {height} - {text} - {font_path}")
        if width is not None:
            width = float(width) * 10
            print (f"{width} - {font_path}")
            height = calculate_text_height(text, font_path, width , letter_spacing)
        elif height is not None:
            height = float(height) * 10
            print (f"{height}")
            width = calculate_text_width(text, font_path, height, letter_spacing)

# Frequent Sizes
# S = 8cm
# M = 10cm
# L = 12cm
# XL = 15cm
# XXL = 18cm
# 2XL = 20cm

        frequent_heights = [80, 100, 120, 150, 180, 200]
        results = calculate_widths_for_heights(text, font_path, frequent_heights)
        return JsonResponse({"Width": width, "Height": height,"frequent_sizes": results})

@session_token_required_api
def all_products(request):

    products = shopify.Product.find()

    return JsonResponse({'products': [p.to_dict() for p in products]})

@csrf_exempt
@session_token_required_api
def create(request):
    if request.method == 'POST':
        try:
            product = shopify.Product()
            product.title = request.POST.get('title','No Title')
            product.published = True
            product.status = 'active'
            product.tags = request.POST.get('tag','neon_product')
            product.images = [{'src':request.POST.get('image',None)}]

            # product.variants = [{'option1':'price',"price":request.POST.get('price',0),'inventory_quantity':1}]
            product.save()
            product_id = product.id
            # Specify the collection ID to which the product should be added
            collection_id = 471810310337  # Replace with your collection's ID

            # Create a collect (assign product to collection)
            collect = shopify.Collect()
            collect.product_id = product_id
            collect.collection_id = collection_id
            collect.save()

            # print(f"Product {product_id} added to collection {collection_id}")

            product.to_json()
            return JsonResponse({'mainProduct':product.to_dict(),'status':'Product created'})
        except Exception as e:
            print(e)
            return JsonResponse({'mainProduct':None,'status':'Product Not Created'})
        
@csrf_exempt
@session_token_required_api
def get_variant(request):
    if(request.method == 'POST'):

        title = request.POST.get('title','unknown')
        price = request.POST.get('price',0)
        tag = request.POST.get('tag','')
        weight = request.POST.get('weight',0)
        weight_unit = request.POST.get('weight_unit','kg')
        requires_shipping = request.POST.get('requires_shipping',True)
        image = request.POST.get('image', 'https://cdn.shopify.com/s/files/1/0765/1301/8186/files/DeinAbschnittstext_9e995925-c218-4626-8d7c-011ebc39e622.png?v=1722331231')
        variant = None
        variant_count = None
        product_id = None

        image_id = None

        try:
            cleint = shopify.GraphQL()
            products = cleint.execute(query='{products(first: 10, reverse: true, query: "tag:'+tag+'"){edges {node {title id featuredImage{id}}}}}')
            products = json.loads(products)
            products = products['data']['products']['edges']
            size = len(products)
            print(size)
            if size > 0:
                product_id = products[0]['node']['id'].rsplit('/', 1)[-1]
                variant_count = shopify.Variant.count(product_id=product_id)
            if size <= 0:
                # create product and get variant
                variant = create_product(title,price,tag,image)
            else:
                if variant_count < 90:
                    variant = createVariant(id=product_id,image=image,title=title,price=price,weight=weight,weight_unit=weight_unit,requires_shipping=requires_shipping)
                else:
                    variant = create_product(title,price,tag,image,weight,weight_unit,requires_shipping)
            return JsonResponse({
                'status':'success',
                'Result': products,
                'count': size,
                'variant': variant,
                'variant_count': variant_count,
                'product_id': product_id
            })
        except Exception as e:
            print("Exception>> ",e)
            return JsonResponse({
                'status':'error',
                'message': 'Something went wrong',
                'description': str(e)
            })

@csrf_exempt
@session_token_required_api    
def update_variant(request):
    if request.method == "POST":
        now = (datetime.now() + timedelta(hours=3)).strftime("%H:%M:%S_%d/%m/%Y")
        title = request.POST.get('title','unknown') +' - '+ now
        variant_id = request.POST.get('variant_id',None)
        price = request.POST.get('price',0)
        try:
            variant = shopify.Variant.find(variant_id)
            variant.option1 = title
            variant.price = price
            variant.save()
            
            print(variant)
            return JsonResponse({'status':True,'variant':variant.to_dict()})
        except Exception as e:
            return JsonResponse({'status':False,'message':str(e)})


@csrf_exempt
@session_token_required_api
def upload_image(request):
    print(request.method)
    if request.method == 'POST':
        image = request.FILES['image']
        print('image',image.name)
        try:
            image_data = base64.b64encode(image.read()).decode('utf-8')
            image = shopify.Image({'product_id':'10486405726401'})
            image.position = 1
            image.attachment = image_data
            image.save()
            return JsonResponse({'status':True})
        except Exception as e:
            print(e)
            return JsonResponse({'status':False,'message':str(e)})        
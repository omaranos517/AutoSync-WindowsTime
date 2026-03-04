from PIL import Image

def convert_to_ico_fixed(input_path, output_path):
    try:
        img = Image.open(input_path).convert("RGBA")
        
        # التأكد من عمل Resize بجودة عالية جداً (LANCZOS)
        img_resized = img.resize((256, 256), Image.Resampling.LANCZOS)
        
        # حفظ بمقاس واحد فقط لضمان أن ويندوز لا يختار الـ 16x16
        img_resized.save(output_path, format='ICO', sizes=[(256, 256)])
        
        print(f"✅ تم الحفظ بمقاس 256x256 حصراً: {output_path}")
    except Exception as e:
        print(f"❌ خطأ: {e}")

convert_to_ico_fixed('icon.png', 'icon_256.ico')
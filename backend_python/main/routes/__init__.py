import base64
import mimetypes


def image2base64(file):
    mime_type, _ = mimetypes.guess_type(file)

    if not mime_type:
        mime_type = 'image/png'
    
    with open(file,"rb") as image_file:
        binary_data = image_file.read()

        base64String = base64.b64encode(binary_data).decode('utf-8')

        return f"data:{mime_type};base64,{base64String}" 

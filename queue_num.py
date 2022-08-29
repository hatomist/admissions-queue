from PIL import Image, ImageDraw, ImageFont
import os.path

PIC_DIR = 'q_nums'


def gen_image(num):
    num = str(num)
    W, H = (640, 360)
    img = Image.new('RGB', (W, H), color='#FFE4C4')
    fnt = ImageFont.truetype('./Montserrat-Bold.ttf', 120)
    d = ImageDraw.Draw(img)
    w, h = d.textsize(num, font=fnt)
    d.text(((W-w)/2, (H-h)/2-16), num, fill='black', font=fnt)
    img.save(open(f'{PIC_DIR}/{num}.jpg', 'w'))


def get_num(num):
    num = str(num)
    if not os.path.exists(f'{PIC_DIR}/{num}.jpg'):
        gen_image(num)
    return f'{PIC_DIR}/{num}.jpg'


def pre_gen_nums(num: int):
    for i in range(num):
        get_num(i)

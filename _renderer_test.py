#!/usr/bin/env python

from PIL import Image
import ass
import ass.renderer
from datetime import timedelta
import sys

doc = ass.document.Document()
doc.scaled_border_and_shadow = "yes"

SCALE = 2
DPI = 72

doc.styles.append(ass.document.Style(
    name="Default",
    shadow=0,
    outline=0,
    alignment=7,
    bold=False,
    margin_l=int(1.25 * DPI * SCALE),
    margin_r=int(1.25 * DPI * SCALE),
    margin_v=0,
    fontname="Garamond",
    fontsize=13 * SCALE,
    primary_color=ass.data.Color.BLACK
))

doc.events.append(ass.document.Dialogue(
    start=timedelta(0),
    end=timedelta(milliseconds=1),
    margin_v=int(0.5 * DPI * SCALE),
    style="Default",
    text="{\\an2}- 1 -"
))

doc.events.append(ass.document.Dialogue(
    start=timedelta(0),
    end=timedelta(milliseconds=1),
    margin_v=int(1.5 * DPI * SCALE),
    style="Default",
    text="""
{\\fs72}Lorem Ipsum{\\r}

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras adipiscing leo
nec lorem vulputate gravida. Maecenas vitae sodales elit. Fusce eget malesuada
neque, sed imperdiet mi. Etiam vel urna aliquam, aliquet nunc et, bibendum leo.
Donec a neque risus. Sed sit amet lectus vel quam imperdiet pulvinar. Donec a
justo vitae metus suscipit dapibus. In lacinia vestibulum vestibulum. Integer
turpis sapien, varius eget mi vel, lobortis congue eros. Aenean euismod urna
non augue ultrices luctus. Morbi mattis pharetra dapibus. Sed egestas est quis
augue faucibus, in porttitor enim porta. Nulla scelerisque tellus ac odio
euismod, at venenatis risus cursus. Sed tincidunt augue nibh. Ut interdum, est
quis mattis dignissim, eros sem pulvinar libero, vel iaculis turpis lorem vitae
tortor. Sed ac nunc in ipsum cursus aliquam.

Curabitur a massa elementum purus condimentum adipiscing. Maecenas dapibus
aliquet eros, vestibulum fermentum diam posuere et. Nulla facilisi. Phasellus
massa neque, auctor vitae fringilla sed, interdum eget magna. Nunc ultrices
sagittis velit, vel sagittis ligula pulvinar nec. Sed in nisi accumsan, gravida
purus a, vehicula nisi. Nam sed felis et urna mattis auctor. Proin non odio
tristique, cursus nibh sed, porttitor lacus. Mauris ultrices purus ut metus
accumsan accumsan id eu lorem. Vivamus non libero tempor, sodales erat sit
amet, iaculis lorem. Aenean pulvinar luctus nulla, non aliquet arcu placerat a.
Sed rhoncus nunc nec pulvinar venenatis. Proin euismod aliquam justo, eget
rhoncus ante interdum vitae.

Curabitur urna nibh, blandit eget massa quis, molestie convallis tellus. Duis
nec metus non lorem hendrerit eleifend a sed mauris. Proin et sapien sit amet
lorem hendrerit ultrices vel eget diam. Donec in euismod nisi. Nunc et tellus
eget tellus cursus semper ac et elit. Duis rhoncus nulla mollis elit bibendum,
quis posuere ligula pharetra. Maecenas urna risus, varius a lorem et, imperdiet
faucibus purus. Vestibulum facilisis leo nec sapien sollicitudin rutrum eu in
enim. Praesent a augue nisl. Praesent sollicitudin dignissim ipsum quis
ultrices.

Pellentesque pellentesque metus ac velit vestibulum, eu semper diam placerat.
Praesent tempor lectus vitae sapien accumsan vulputate. Duis porttitor massa
sit amet felis rhoncus, a auctor lorem hendrerit. Vestibulum cursus metus vel
blandit feugiat. Vivamus dignissim diam sed mauris pellentesque euismod. Mauris
a fermentum ipsum. Praesent quis sapien ultrices, aliquet quam non, lacinia
lacus. Sed interdum risus vel turpis molestie dictum. Quisque vel placerat
tortor, id hendrerit mi. Curabitur blandit enim vel nisl volutpat rutrum.
Quisque molestie pharetra augue, id dapibus mi facilisis ac. Pellentesque
habitant morbi tristique senectus et netus et malesuada fames ac turpis
egestas. Vivamus consectetur lacus ut lacinia gravida. Aenean interdum ac
mauris vitae lacinia. Class aptent taciti sociosqu ad litora torquent per
conubia nostra, per inceptos himenaeos.

Vivamus sit amet felis urna. Donec pulvinar iaculis mi, non posuere lectus
eleifend non. Ut a mi et nulla pretium semper. Donec placerat egestas
fringilla. Sed scelerisque lorem et orci vestibulum egestas. Vestibulum mattis
dolor at eros facilisis hendrerit. Aliquam ac nisi eget velit tempus ornare.
Quisque vel elementum lacus. Pellentesque ornare ligula eget dictum consequat.
Nam id urna et nunc tempus auctor. Nullam nec ornare justo. Fusce auctor
viverra nibh, vitae sodales leo lacinia at. Quisque sed nisi nibh. Aliquam
pellentesque ligula id orci auctor convallis. Etiam et nisl sagittis,
malesuada enim sit amet, malesuada ante.
""".strip().replace("\n\n", "\\N\\N").replace("\n", " ")))

SIZE = (int(8.5 * DPI * SCALE), int(11 * DPI * SCALE))

doc.play_res_x, doc.play_res_y = SIZE
doc.wrap_style = 1

ctx = ass.renderer.Context()

r = ctx.make_renderer()
r.set_fonts(fontconfig_config="\0")
r.set_all_sizes(SIZE)

sys.stdout.write("loading document... ")
sys.stdout.flush()
t = ctx.make_track()
t.populate(doc)
print("ok! {} styles, {} events".format(len(t.styles), len(t.events)))

im_out = Image.new("RGB", SIZE, 0xffffff)
im_data = im_out.load()

for img in r.render_frame(t, timedelta(0)):
    r, g, b, a = img.rgba

    for y in range(img.h):
        for x in range(img.w):
            a_src = img[x, y] * (256 - a) // 256
            r_dst, g_dst, b_dst = im_data[x + img.dst_x, y + img.dst_y]
            r_out = ((r * a_src) + (r_dst * (256 - a_src))) // 256
            g_out = ((g * a_src) + (g_dst * (256 - a_src))) // 256
            b_out = ((b * a_src) + (b_dst * (256 - a_src))) // 256
            im_data[x + img.dst_x, y + img.dst_y] = (r_out, g_out, b_out)

im_out.show()

im_out.save("test.png")

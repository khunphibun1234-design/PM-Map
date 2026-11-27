import base64, json, sys
out = sys.argv[1]
b64 = lambda f: base64.b64encode(open(f, 'rb').read()).decode()
from PIL import Image
Image.open(f'{out}/splatmap_preview.png').convert('RGB').resize((1024,1024)).save(f'{out}/_splat_small.png', optimize=True)
s = open('gen/template_v2.html').read()
s = s.replace('__ALBEDO__', b64(f'{out}/albedo_2048.jpg')).replace('__SPLAT__', b64(f'{out}/_splat_small.png')).replace('__LOGO__', b64('/home/claude/logo/logo_384.png')).replace('__BOY__', b64('/home/claude/site/boy_new.glb')).replace('__GIRL__', b64('/home/claude/site/girl.glb')).replace('__PORTRAIT_L__', b64('/home/claude/site/portraits/left.jpg')).replace('__PORTRAIT_R__', b64('/home/claude/site/portraits/right.jpg')).replace('__PORTRAIT_E__', b64('/home/claude/site/portraits/easel.jpg')).replace('__BUDDHA__', b64('/home/claude/site/buddha.glb'))
s = s.replace('__HEIGHT__', b64(f'{out}/height_257.u16')).replace('__LAYOUT__', open(f'{out}/layout.json').read())
open('school_map_3d_v2.html', 'w').write(s)
print(len(s)/1e6, 'MB')

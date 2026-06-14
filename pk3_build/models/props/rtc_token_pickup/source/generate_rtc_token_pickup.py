#!/usr/bin/env python3
import datetime,email.message,hashlib,json,math,os,pathlib,shutil,smtplib,struct,textwrap
from email.utils import formatdate, make_msgid
BASE=pathlib.Path('/home/linuxuser/.hermes/profiles/lea/earn_ops')
SECRET=pathlib.Path('/home/linuxuser/.hermes/profiles/lea/secrets/email_ovh_lea.json')
RTC='RTC31ede8c0133d0af78ab557d1be7568523b619a84'
HOT='0xd8c4732Aba301F2A5dedcA71603210890616cAC7'
NOW=datetime.datetime.now(datetime.timezone.utc); TS=NOW.strftime('%Y%m%dT%H%M%SZ')
SLUG=f'xonotic_rtc_token_pickup_issue14015_{TS}'
for d in ['work','deliverables','submissions','proofs','logs']:(BASE/d).mkdir(parents=True,exist_ok=True)
work=BASE/'work'/SLUG; prop=work/'pk3_build'/'models'/'props'/'rtc_token_pickup'; prop.mkdir(parents=True,exist_ok=True)

def pack_name(s,n=64):
    b=s.encode('ascii','ignore')[:n-1]; return b+b'\0'*(n-len(b))
def normal16(nx,ny,nz):
    if nx==0 and ny==0: lat=0 if nz>=0 else 128; lng=0
    else:
        lat=int(math.acos(max(-1,min(1,nz)))*255/(2*math.pi))&255; lng=int(math.atan2(ny,nx)*255/(2*math.pi))&255
    return (lat<<8)|lng
verts=[]; tris=[]; sts=[]; norms=[]
def add_tri(a,b,c,n,uv=((.5,0),(1,1),(0,1))):
    i=len(verts); verts.extend([a,b,c]); norms.extend([n,n,n]); sts.extend(uv); tris.append((i,i+1,i+2))
def add_box(x0,y0,z0,x1,y1,z1,nscale=1):
    faces=[((x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1),(0,-1,0)),((x1,y1,z0),(x0,y1,z0),(x0,y1,z1),(x1,y1,z1),(0,1,0)),((x0,y1,z0),(x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(-1,0,0)),((x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1),(1,0,0)),((x0,y1,z1),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(0,0,1)),((x0,y0,z0),(x0,y1,z0),(x1,y1,z0),(x1,y0,z0),(0,0,-1))]
    for a,b,c,d,n in faces:
        i=len(verts); verts.extend([a,b,c,d]); norms.extend([n]*4); sts.extend([(0,1),(1,1),(1,0),(0,0)]); tris.extend([(i,i+1,i+2),(i,i+2,i+3)])
# coin: thick 24-sided cylinder oriented vertical, with raised RTC glyph and glow stand
R=34; W=7; seg=24
for j,z in enumerate([-W,W]):
    center=(0,0,z); n=(0,0,-1 if z<0 else 1)
    for i in range(seg):
        a=2*math.pi*i/seg; b=2*math.pi*(i+1)/seg
        p1=(R*math.cos(a),R*math.sin(a),z); p2=(R*math.cos(b),R*math.sin(b),z)
        if z>0: add_tri(center,p1,p2,n,((.5,.5),((math.cos(a)+1)/2,(math.sin(a)+1)/2),((math.cos(b)+1)/2,(math.sin(b)+1)/2)))
        else: add_tri(center,p2,p1,n,((.5,.5),((math.cos(b)+1)/2,(math.sin(b)+1)/2),((math.cos(a)+1)/2,(math.sin(a)+1)/2)))
for i in range(seg):
    a=2*math.pi*i/seg; b=2*math.pi*(i+1)/seg
    p=[(R*math.cos(a),R*math.sin(a),-W),(R*math.cos(b),R*math.sin(b),-W),(R*math.cos(b),R*math.sin(b),W),(R*math.cos(a),R*math.sin(a),W)]
    n=(math.cos((a+b)/2),math.sin((a+b)/2),0); idx=len(verts); verts.extend(p); norms.extend([n]*4); sts.extend([(i/seg,1),((i+1)/seg,1),((i+1)/seg,0),(i/seg,0)]); tris.extend([(idx,idx+1,idx+2),(idx,idx+2,idx+3)])
# raised RTC strokes on front face
add_box(-21,-3,8,-7,3,12); add_box(-21,-3,8,-17,3,24); add_box(-21,-3,20,-7,3,24); add_box(-13,-3,8,-9,3,17)
add_box(-4,-3,8,0,3,24); add_box(-10,-3,20,6,3,24)
add_box(10,-3,8,14,3,24); add_box(10,-3,20,25,3,24); add_box(10,-3,8,25,3,12)
# transparent-ish pickup halo frame / base (actual alpha handled by shader if desired)
add_box(-42,-42,-11,42,-38,-7); add_box(-42,38,-11,42,42,-7); add_box(-42,-42,-11,-38,42,-7); add_box(38,-42,-11,42,42,-7)
# small vertical sparkle rods
for ang in [0,math.pi/2,math.pi,3*math.pi/2]: add_box(44*math.cos(ang)-1,44*math.sin(ang)-1,-4,44*math.cos(ang)+1,44*math.sin(ang)+1,28)
xyz=b''.join(struct.pack('<hhhH',int(round(x)),int(round(y)),int(round(z)),normal16(*norms[i])) for i,(x,y,z) in enumerate(verts))
tri=b''.join(struct.pack('<iii',*t) for t in tris); shader=pack_name('models/props/rtc_token_pickup/rtc_token_pickup')+struct.pack('<i',0); st=b''.join(struct.pack('<ff',*uv) for uv in sts)
surf_header_size=108; ofs_tri=surf_header_size; ofs_shader=ofs_tri+len(tri); ofs_st=ofs_shader+len(shader); ofs_xyz=ofs_st+len(st); ofs_end=ofs_xyz+len(xyz)
surf=struct.pack('<4s64s10i',b'IDP3',pack_name('rtc_token_pickup'),0,1,1,len(verts),len(tris),ofs_tri,ofs_shader,ofs_st,ofs_xyz,ofs_end)+tri+shader+st+xyz
frame=struct.pack('<3f3f3ff16s',-46,-46,-12,46,46,28,0,0,8,70,b'frame0'+b'\0'*10)
header_size=108; ofs_frames=header_size; ofs_tags=ofs_frames+len(frame); ofs_surfaces=ofs_tags; ofs_end=ofs_surfaces+len(surf)
header=struct.pack('<4si64s9i',b'IDP3',15,pack_name('rtc_token_pickup'),0,1,0,1,0,ofs_frames,ofs_tags,ofs_surfaces,ofs_end)
(prop/'rtc_token_pickup.md3').write_bytes(header+frame+surf)
try:
    from PIL import Image, ImageDraw
    img=Image.new('RGB',(256,256),(12,9,2)); dr=ImageDraw.Draw(img)
    for r,c in [(124,(255,135,24)),(108,(255,190,45)),(84,(255,230,85)),(64,(255,145,30))]: dr.ellipse((128-r,128-r,128+r,128+r),outline=c,width=7)
    dr.text((74,104),'RTC',fill=(40,18,0)); dr.text((70,100),'RTC',fill=(255,255,170))
    for x in range(0,256,16): dr.line((x,0,255-x,255),fill=(80,45,0))
    img.save(prop/'rtc_token_pickup.tga'); img.resize((512,512)).save(prop/'preview.png')
except Exception as e: (prop/'texture_note.txt').write_text(repr(e))
(prop/'rtc_token_pickup.skin').write_text('rtc_token_pickup,models/props/rtc_token_pickup/rtc_token_pickup.tga\n')
(prop/'rtc_token_pickup.shader').write_text('''models/props/rtc_token_pickup/rtc_token_pickup\n{\n  qer_editorimage models/props/rtc_token_pickup/rtc_token_pickup.tga\n  { map models/props/rtc_token_pickup/rtc_token_pickup.tga rgbGen identity }\n}\n''')
(prop/'rtc_token_pickup_prefab.map').write_text('''// NetRadiant prefab: RTC token pickup prop\n{\n"classname" "misc_model"\n"model" "models/props/rtc_token_pickup/rtc_token_pickup.md3"\n"origin" "0 0 32"\n"angle" "0"\n}\n{\n"classname" "light"\n"origin" "0 0 48"\n"light" "180"\n"_color" "1.0 0.65 0.08"\n}\n''')
(prop/'LICENSE').write_text('Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA-4.0). Original asset generated for Xonotic RustChain Arena.\n')
(prop/'README.md').write_text(textwrap.dedent(f'''# RTC Token Pickup — Xonotic RustChain Arena prop\n\nSubmission for Scottcjn/rustchain-bounties issue #14015, wishlist item: **RTC token pickup (spinning coin / item model)**.\n\nContents: generated MD3 model, 256x256 TGA texture, .skin, simple shader, NetRadiant prefab, preview image, license, manifest, and deterministic source generator.\n\nTheme fit: a gold RTC coin with raised RTC lettering, halo/base frame, and glow rods. It can be used as a pickup/reward-loop placeholder or map set dressing.\n\nGeometry: {len(verts)} vertices / {len(tris)} triangles.\n\nClaim: RTC wallet `{RTC}`; EVM fallback `{HOT}`.\n'''))
src=prop/'source'; src.mkdir(); (src/'generate_rtc_token_pickup.py').write_text(pathlib.Path(__file__).read_text())
md3=(prop/'rtc_token_pickup.md3').read_bytes(); valid=md3[:4]==b'IDP3' and struct.unpack('<i',md3[4:8])[0]==15 and len(md3)>500
manifest=[]
for p in sorted(work.rglob('*')):
    if p.is_file(): manifest.append({'path':str(p.relative_to(work)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(work/'MANIFEST.json').write_text(json.dumps({'time':NOW.isoformat(),'md3_valid_header':valid,'vertices':len(verts),'triangles':len(tris),'files':manifest},indent=2))
(work/'SUBMISSION.md').write_text(textwrap.dedent(f'''# Submission: RTC Token Pickup prop for Xonotic RustChain Arena (#14015)\n\nDelivered a distinct wishlist prop: **RTC token pickup (spinning coin / item model)**.\n\n- Bounty: https://github.com/Scottcjn/rustchain-bounties/issues/14015\n- Asset path: `pk3_build/models/props/rtc_token_pickup/`\n- Main model: `rtc_token_pickup.md3`\n- Texture: `rtc_token_pickup.tga` (256x256 power-of-two)\n- Geometry: {len(verts)} verts, {len(tris)} triangles\n- License: CC-BY-SA-4.0 / GPL-compatible\n- MD3 validation: IDP3/version 15 = `{valid}`\n- RTC wallet: `{RTC}`\n- EVM fallback: `{HOT}`\n\nNo GitHub PR/comment could be opened unattended (no authenticated GitHub token/account in this profile), so this package is submitted transparently by email with attachment.\n'''))
zip_path=BASE/'deliverables'/f'{SLUG}.zip'; shutil.make_archive(str(zip_path.with_suffix('')),'zip',work); sha=hashlib.sha256(zip_path.read_bytes()).hexdigest(); (zip_path.with_suffix(zip_path.suffix+'.sha256')).write_text(f'{sha}  {zip_path.name}\n')
sec=json.loads(SECRET.read_text())
body=textwrap.dedent(f'''Hi Scott,\n\nSubmitting one more distinct prop for rustchain-bounties #14015: the wishlist item "RTC token pickup (spinning coin / item model)".\n\nPackage summary:\n- `pk3_build/models/props/rtc_token_pickup/rtc_token_pickup.md3`\n- gold RTC coin with raised RTC letters, halo/base frame, glow rods; designed as pickup/reward-loop placeholder or map dressing\n- 256x256 power-of-two TGA texture + .skin + simple shader\n- optional NetRadiant prefab, README, LICENSE, source generator, manifest\n- geometry: {len(verts)} verts, {len(tris)} triangles\n- MD3 header validation: IDP3 / version 15 = {valid}\n- SHA256(zip): {sha}\n\nClaim/payment:\n- RTC wallet: {RTC}\n- EVM fallback: {HOT}\n\nOperational note: I still cannot open a GitHub PR/comment unattended from this profile, so I am submitting transparently by email with the zip attached.\n\nBest,\nLéa / Kryosys\n''')
msg=email.message.EmailMessage(); msg['From']=sec['email']; msg['To']='scott@elyanlabs.ai'; msg['Subject']='RustChain bounty #14015 submission — RTC Token Pickup prop'; msg['Date']=formatdate(localtime=False); msg['Message-ID']=make_msgid(domain='getprivebot.fr'); msg.set_content(body); msg.add_attachment(zip_path.read_bytes(),maintype='application',subtype='zip',filename=zip_path.name)
eml=BASE/'submissions'/f'email_rtc_token_pickup_issue14015_{TS}.eml'; eml.write_bytes(bytes(msg))
proof={'time':NOW.isoformat(),'to':msg['To'],'subject':msg['Subject'],'zip':str(zip_path),'sha256':sha,'sent':False}
try:
    with smtplib.SMTP(sec.get('smtp_host','ssl0.ovh.net'),int(sec.get('smtp_port',587)),timeout=60) as s:
        s.starttls(); s.login(sec['email'],sec['password']); s.send_message(msg)
    proof['sent']=True
except Exception as e: proof['error']=repr(e)
proof_path=BASE/'proofs'/f'smtplib_send_rtc_token_pickup_issue14015_{TS}.json'; proof_path.write_text(json.dumps(proof,indent=2,ensure_ascii=False))
report=BASE/'logs'/f'cron_local_report_rtc_token_pickup_issue14015_{TS}.md'; report.write_text(textwrap.dedent(f'''# Earn ops local report — {TS}\n\n## Action executed\nCreated and submitted a distinct Xonotic RustChain Arena prop for bounty #14015: **RTC Token Pickup**.\n\n## Artifacts\n- Workdir: `{work}`\n- Zip: `{zip_path}`\n- SHA256: `{sha}`\n- Email draft: `{eml}`\n- Send proof: `{proof_path}`\n\n## Verification\n- Generated MD3 file has `IDP3` header and version 15: `{valid}`.\n- Geometry: {len(verts)} vertices / {len(tris)} triangles.\n- Package includes MD3, TGA texture, skin, shader, prefab, README, LICENSE, manifest and source generator.\n- Email sent: `{proof.get('sent')}`.\n\n## Safety\nNo KYC/CAPTCHA/phone/2FA bypass, no deposits, no on-chain signing, no private keys, no off-scope hacking. This is a requested public creative bounty and was sent only to the already-established maintainer contact.\n'''))
status_path=BASE/'status.json'
try: st=json.loads(status_path.read_text())
except Exception: st={}
entry={'platform':'GitHub/public email','listing':'RustChain Xonotic prop bounty #14015 — RTC Token Pickup','listing_url':'https://github.com/Scottcjn/rustchain-bounties/issues/14015','status':'submitted_by_email_attachment' if proof.get('sent') else 'local_deliverable_send_failed','reward_pool':'7 RTC per accepted prop','submitted_at':NOW.isoformat(),'contact':'scott@elyanlabs.ai','sha256':sha,'payment':{'rtc_wallet':RTC,'evm_fallback':HOT},'artifacts':{'zip':str(zip_path),'email':str(eml),'send_proof':str(proof_path),'report':str(report)}}
st['time']=NOW.isoformat(); st['last_action']='Submitted RustChain #14015 RTC token pickup prop by email attachment.'; st['cash_received']=st.get('cash_received',False); st.setdefault('submissions',[]).append(entry); st['latest_rtc_token_pickup_issue14015_submission']=str(eml); st['latest_rtc_token_pickup_issue14015_artifact']=str(zip_path); st.setdefault('artifacts',[]).extend([str(zip_path),str(zip_path.with_suffix(zip_path.suffix+'.sha256')),str(eml),str(proof_path),str(report)])
status_path.write_text(json.dumps(st,indent=2,ensure_ascii=False))
print(json.dumps({'sent':proof.get('sent'),'zip':str(zip_path),'sha256':sha,'report':str(report),'valid':valid,'vertices':len(verts),'triangles':len(tris)},indent=2))

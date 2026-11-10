import io
p='ivm_bake.py'
s=io.open(p,encoding='utf-8').read()
old="""    print("%-9s %-26s mean=%.4f sd=%.4f min=%.3f max=%.3f | cov>.5=%.3f cov>.1=%.3f "
          "| chord>.5 = %.1fpx = %.1fcm (%d runs)"
          % (label, title, mean, sd, s[0], s[-1], cov50, cov10,
             chord, chord / size * TILE_M * 100, ncnt))"""
new="""    med = s[n // 2]
    print("%-9s %-24s mean=%.4f med=%.4f sd=%.4f min=%.3f max=%.3f | cov>.5=%.3f cov>.1=%.3f "
          "| chord>.5 = %.1fpx = %.1fcm (%d runs)"
          % (label, title, mean, med, sd, s[0], s[-1], cov50, cov10,
             chord, chord / size * TILE_M * 100, ncnt))"""
assert s.count(old)==1
s=s.replace(old,new)
old2="""    for lab, ttl in (('CLOUDF', 'slab tone factor'),
                     ('MOTTF', 'mottle factor'),
                     ('FINEF', 'hairline vein mask'),
                     ('GATEF', 'bold vein gate'),
                     ('BOLDF', 'bold vein factor')):"""
new2="""    for lab, ttl in (('CNRAW', 'raw slab noise'),
                     ('MNRAW', 'raw mottle noise'),
                     ('FNRAW', 'raw hairline noise'),
                     ('GNRAW', 'raw bold noise'),
                     ('GMRAW', 'raw gate noise'),
                     ('CLOUDF', 'slab tone factor'),
                     ('MOTTF', 'mottle factor'),
                     ('FINEF', 'hairline vein mask'),
                     ('GATEF', 'bold vein gate'),
                     ('BOLDF', 'bold vein factor')):"""
assert s.count(old2)==1
s=s.replace(old2,new2)
io.open(p,'w',encoding='utf-8').write(s)
print("patched bake")

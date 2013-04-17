from django.core.serializers import serialize
from cams.models import Person, Organisation, Contactable, Contact

for m in [Person, Organisation, Contactable, Contact]:
    plural = unicode(m._meta.verbose_name_plural)
    print(plural)
    fout = open('{0}.xml'.format(plural), 'w')
    fout.write(serialize('xml', m.objects.all()))
    fout.close()


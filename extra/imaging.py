# MRWF - extra/imaging.py
#
# Copyright (C) 2009, 2010, 2011. 2012, 2013
# Guillaume Tucker <guillaume@mangoz.org>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

import Image
import os

def scale_down(img_field, max_D, max_d):
    if (max_d > max_D):
        tmp = max_d
        max_d = max_D
        max_D = max_d

    try:
        file_name = os.path.split(img_field.path)[1]
        img = Image.open(img_field)
        format = img.format

        if (format != "JPEG") and (format != "PNG") and (format != "GIF"):
            format = "JPEG"
            file_name = os.path.splitext(file_name)[0] + ".jpeg"
            save = True
        else:
            save = False

        if img.size[0] > img.size[1]:
            D = img.size[0]
            d = img.size[1]
        else:
            D = img.size[1]
            d = img.size[0]

        if D > max_D:
            ratio = float(max_D) / float(D)
            d *= ratio
        else:
            ratio = 1.0

        if d > max_d:
            ratio *= (float(max_d) / float(d))

        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))

        if img.size != new_size:
            img = img.resize(new_size, Image.ANTIALIAS)
            save = True

        if save:
            new_name = img_field.field.generate_filename(img_field.instance,
                                                         file_name)
            img_field.name = new_name
            img.save(img_field.path, format)
            img_field._size = os.path.getsize(img_field.path)
            img_field._committed = True

        ret = True

    except IOError:
        # ToDo: do not save anything, or save the original?
        ret = False

    return ret

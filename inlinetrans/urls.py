# Copyright (c) 2010-2013 by Yaco Sistemas <ant30tx@gmail.com> or <goinnn@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this programe.  If not, see <http://www.gnu.org/licenses/>.

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^apply_changes/$', views.do_restart, name='apply_changes'),
    url(r'^set_new_translation/$', views.set_new_translation, name='set_new_translation'),
]


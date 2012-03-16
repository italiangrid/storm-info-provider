dnl Copyright (c) Istituto Nazionale di Fisica Nucleare (INFN). 2006-2010.
dnl
dnl Licensed under the Apache License, Version 2.0 (the "License");
dnl you may not use this file except in compliance with the License.
dnl You may obtain a copy of the License at
dnl
dnl     http://www.apache.org/licenses/LICENSE-2.0
dnl
dnl Unless required by applicable law or agreed to in writing, software
dnl distributed under the License is distributed on an "AS IS" BASIS,
dnl WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
dnl See the License for the specific language governing permissions and
dnl limitations under the License.

dnl Usage:
dnl - LIBTYPE
dnl - DISTTAR

dnl - STORM_CLIENT_LOCATION
dnl - STORM_CLIENT_CFLAGS
dnl - STORM_CLIENT_LDFLAGS

dnl - STORM_FRONTEND_LOCATION
dnl - STORM_FRONTEND_CFLAGS
dnl - STORM_FRONTEND_LDFLAGS

dnl - STORM_GRIDFTP_LOCATION
dnl - STORM_GRIDFTP_CFLAGS
dnl - STORM_GRIDFTP_LDFLAGS

AC_DEFUN([AC_STORM],
[
    AC_ARG_WITH(dist_bin_location,
                [  --with-dist-bin-location=PFX     prefix where DIST location is. (pwd)],
                [],
                with_dist_bin_location=$WORKDIR/../dist
               )

    DISTBIN=$with_dist_bin_location
    AC_SUBST([DISTBIN])

    AC_ARG_WITH(dist_source_location,
                [  --with-dist-source-location=PFX     prefix where DIST location is. (pwd)],
                [],
                with_dist_source_location=$WORKDIR/../dist
               )

    DISTSOURCE=$with_dist_source_location
    AC_SUBST([DISTSOURCE])

    AC_ARG_WITH(module_location,
                [  --with-module-location=PFX     prefix where module location is. (pwd)],
                [],
                with_module_location=$PWD
               )

    MODULELOCATION=$with_module_location
    AC_SUBST([MODULELOCATION])

    if test "x$host_cpu" = "xx86_64"; then
        AC_SUBST([libdir], ['${exec_prefix}/lib64'])
        libtype='lib64'
    else
        libtype='lib'
    fi

    AC_SUBST([LIBTYPE], [$libtype])
    AC_SUBST([mandir], ['${prefix}/share/man'])

])

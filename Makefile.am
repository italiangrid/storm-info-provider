# Copyright (c) Istituto Nazionale di Fisica Nucleare (INFN). 2006-2010.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Authors: Elisabetta Ronchieri <elisabetta.ronchieri@cnaf.infn.it>
#

EXTRA_DIST = \
    AUTHORS \
    bootstrap \
    ChangeLog \
    README \
    LICENSE \
    CREDITS \
    storm-dynamic-info-provider.spec.in \
    project \
    m4

docdir = $(datadir)/doc/@PACKAGE@-@VERSION@
doc_DATA = AUTHORS \
    LICENSE \
    CREDITS \
    ChangeLog \
    README

## Subdirectories list
SUBDIRS = etc

## Default flags to run aclocal
ACLOCAL_AMFLAGS = -I m4

CLEANFILES = \
    storm-dynamic-info-provider.spec

MAINTAINERCLEANFILES = Makefile.in

SPEC_FILE = \
    storm-dynamic-info-provider.spec

RPM_MAIN_DIR = $(PWD)/rpm
RPM_TMP_DIR = $(RPM_MAIN_DIR)/tmp
RPM_SOURCE = $(RPM_MAIN_DIR)/SOURCES
RPM_SPEC = $(RPM_MAIN_DIR)/SPECS
RPM_BUILD = $(RPM_MAIN_DIR)/BUILD
RPM_RPM = $(RPM_MAIN_DIR)/RPMS
RPM_SRPM = $(RPM_MAIN_DIR)/SRPMS
RPM_DIRS = $(RPM_MAIN_DIR) $(RPM_SOURCE) $(RPM_SPEC) $(RPM_BUILD) $(RPM_RPM) $(RPM_SRPM)

rpm: dist
	/bin/mkdir -p $(RPM_DIRS)
	/bin/cp -u @PACKAGE@-@VERSION@.tar.gz $(RPM_SOURCE)
	/bin/cp $(SPEC_FILE) $(RPM_SPEC)
	cd $(RPM_SPEC); \
        /usr/bin/rpmbuild  --define "_topdir $(RPM_MAIN_DIR)" --nodeps -ba $(RPM_SPEC)/$(SPEC_FILE)
	mkdir -p @DISTSOURCE@ @DISTBIN@

stage:
	@set fnord $(MAKEFLAGS); amf=$$2; \
        dot_seen=no; \
        target="install"; \
        prefix_arg="@prefix@"; \
        list='$(SUBDIRS)'; for subdir in $$list; do \
          echo "Making $$target $$prefix_arg in $$subdir"; \
          if test "$$subdir" = "."; then \
            dot_seen=yes; \
            local_target="$$target-am"; \
          else \
            local_target="$$target"; \
          fi; \
          (cd $$subdir && $(MAKE) $(AM_MAKEFLAGS) $$local_target $$prefix_arg) \
           || case "$$amf" in *=*) exit 1;; *k*) fail=yes;; *) exit 1;; esac; \
	done; \
        if test "$$dot_seen" = "no"; then \
          $(MAKE) $(AM_MAKEFLAGS) "$$target-am" $$prefix_arg || exit 1; \
        fi; test -z "$$fail"

distsrc:
	mkdir -p @DISTSOURCE@
	cp $(distdir).tar.gz @DISTSOURCE@/$(distdir)-@STORM_UTILITY_AGE_NUMBER@.@STORM_UTILITY_SO@.src.tar.gz
	cp $(RPM_SRPM)/*.rpm @DISTSOURCE@

distbin: stage  
	mkdir -p @DISTBIN@; \
	cd etics-tmp; tar -zcf $(distdir).noarch.tar.gz etc usr; cp $(distdir).noarch.tar.gz @DISTBIN@/$(distdir)-@STORM_UTILITY_AGE_NUMBER@.@STORM_UTILITY_SO@.noarch.tar.gz; cd ..; \
	cp $(RPM_RPM)/*/*.rpm @DISTBIN@

clean-local:
	rm -f @PACKAGE@-@VERSION@.*.tar.gz 

distclean-local:
	rm -rf $(RPM_DIRS) project 

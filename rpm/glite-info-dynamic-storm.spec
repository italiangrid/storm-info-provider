# 
# RPM spec file for the StoRM dynamic information provider plugin
#
# Copyright (c) 2008 Magnoni Luca <luca.magnoni@cnaf.infn.it>.
# 
# You may copy, modify and distribute this file under the same
# terms as the StoRM itself.
#
#


### Package Naming 

Name: glite-info-dynamic-storm
Version: 1.5.0
Release: 6.sl4
Summary: The StoRM dynamic information provider plugin.
#Copyright:  Apache License, Version 2.0. 
License:  Apache License, Version 2.0
Url: http://storm.forge.cnaf.infn.it
Vendor: INFN - CNAF (2010)
Group: Application/Generic
Packager: Luca Magnoni <luca.magnoni@cnaf.infn.it> 
Prefix: /opt/glite
BuildRoot: %{_topdir}/BUILD/glite-info-dynamic-storm-1.5.0
Source: %{name}-%{version}.tar.gz


### Package Description

%description
This package contains the StoRM dynamic information provider plugin.
This plugin provides dynamic information on space usage and other parameters published by the StoRM Storage Element.

###### Package Dependency



%files
%defattr(755,root,root)
%{prefix}/libexec/glite-info-dynamic-storm
%{prefix}/libexec/glite-info-service-storm
%{prefix}/etc/glite-info-service-srm-storm-v2.conf.template

%prep
%setup -n glite-info-dynamic-storm-1.5.0




# SPDX-FileCopyrightText: 2010 Istituto Nazionale di Fisica Nucleare
#
# SPDX-License-Identifier: Apache-2.0

%define _confdir /etc/storm/info-provider
%define _bdiidir /var/lib/bdii/gip

# Remember to define the base_version macro
%{!?base_version: %global base_version 0.0.0}
%global slash_name storm/webdav

Name: storm-info-provider
Version: %{base_version}
Release: 1%{?dist}
Summary: The StoRM info provider component

Group: Development/Libraries
License: Apache-2.0
URL: https://github.com/italiangrid/storm-info-provider

BuildArch: noarch

BuildRequires: python3-devel
BuildRequires: python3-ldap

Requires: python3
Requires: python3-ldap
Requires: bdii

%description
This is the installation bundle for the StoRM info provider component.

%prep

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}

install -d %{buildroot}%{_libexecdir}
install -pm 0755 src/storm-info-provider %{buildroot}%{_libexecdir}

install -d %{buildroot}%{python3_sitelib}/info_provider
install -d %{buildroot}%{python3_sitelib}/info_provider/glue
install -d %{buildroot}%{python3_sitelib}/info_provider/model
install -d %{buildroot}%{python3_sitelib}/info_provider/utils
install -pm 0644 src/info_provider/glue/* %{buildroot}%{python3_sitelib}/info_provider/glue
install -pm 0644 src/info_provider/model/* %{buildroot}%{python3_sitelib}/info_provider/model
install -pm 0644 src/info_provider/utils/* %{buildroot}%{python3_sitelib}/info_provider/utils
install -pm 0644 src/info_provider/*.py %{buildroot}%{python3_sitelib}/info_provider

install -d %{buildroot}%{_confdir}
install -d %{buildroot}%{_confdir}/templates
install -pm 0755 config/templates/* %{buildroot}%{_confdir}/templates

%files
%defattr(-,root,root,-)
%{_libexecdir}/storm-info-provider
%{python3_sitelib}/info_provider
%{_confdir}/templates

%postun
rm -rf %{_bdiidir}/ldif/storm-glue2-static.ldif
rm -rf %{_bdiidir}/provider/storm-glue2-provider
rm -rf %{_bdiidir}/plugin/storm-glue2-plugin

%changelog

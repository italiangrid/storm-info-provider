The StoRM Info Provider
===============================

StoRM Info Provider is the component of StoRM deployment in charge of feeding resource BDII with 
information on the Grid Storage Element and the status of its Storage Areas. It produces ldif
files populated by gatering information from StoRM BackEnd.

Supported platforms
Scientific Linux 5 on x86_64 architecture
Scientific Linux 6 on x86_64 architecture

### Building
Required packages:

* epel
* git
* automake
* autoconf
* libtool
* gcc
* rpm-build

Build command:
```bash
./bootstrap
./configure --prefix=/usr --libexecdir=/usr/libexec --sysconfdir=/etc --datadir=/usr/share
make rpm
```

# Contact info

If you have problems, questions, ideas or suggestions, please contact us at
the following URLs

* GGUS (official support channel): http://www.ggus.eu

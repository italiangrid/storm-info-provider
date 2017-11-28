# storm-info-provider(1) -- Publish StoRM storage service information

## SYNOPSIS

`/usr/libexec/storm-info-provider` <options> `configure`|`get-static-ldif`|`get-update-ldif`|`get-report-json` <options>

## DESCRIPTION

StoRM Info Provider is the component of StoRM in charge of:

* feeding resource BDII with information on the Grid Storage Element and the status of its Storage Areas;
* export a JSON report for storage resource reporting in WLCG.

To feed resource BDII, it produces ldif files populated by gatering information from both YAIM configuration and StoRM Backend service.

## USAGE

StoRM Info Provider is the following runnable Python script:

`/usr/libexec/storm-info-provider`

which can be executed by specifying a specific action:

* `configure`
* `get-static-ldif`
* `get-update-ldif`
* `get-report-json`

### /usr/libexec/storm-info-provider configure

The `configure` action installs/creates all the necessary files to make BDII able to retrieve information from StoRM service and publish them by following the needed GLUE specifications. It's automatically re-run during StoRM service YAIM configuration. Knowing that, by default, the BDII uses the following three directories to obtain information sources:

```
/var/lib/bdii/gip/ldif
/var/lib/bdii/gip/provider
/var/lib/bdii/gip/plugin
```

These directories are specified as configuration parameters in the BDII's configuration (see http://gridinfo.web.cern.ch/developers/resource-bdii). StoRM info provider configure action, by default, creates the provider, plugin and static LDIF file for both GLUE v1.3 and GLUE v2 specifications:

```
/var/lib/bdii/gip/plugin/storm-glue13-plugin
/var/lib/bdii/gip/provider/storm-glue13-provider
/var/lib/bdii/gip/static/storm-glue13-static.ldif
/var/lib/bdii/gip/plugin/storm-glue2-plugin
/var/lib/bdii/gip/provider/storm-glue2-provider
/var/lib/bdii/gip/static/storm-glue2-static.ldif
```

The configure action creates also several configuration files, used by the providers scripts:

```
/etc/storm/info-provider/glite-info-glue2-service-storm-endpoint-webdav.conf
/etc/storm/info-provider/glite-info-glue13-service-storm.conf
/etc/storm/info-provider/glite-info-glue2-service-storm-endpoint-srm.conf
/etc/storm/info-provider/glite-info-glue2-service-storm.conf
```

The configure action also build the WLCG JSON report to:

```
/etc/storm/info-provider/site-report.json
```

by default.

### /usr/libexec/storm-info-provider get-static-ldif

The `get-static-ldif` action can be used to obtain the static LDIF of a particular GLUE specification version. This output is the same content of the LDIF file saved into /var/lib/bdii/gip/static directory during configure execution.

### /usr/libexec/storm-info-provider get-update-ldif

The `get-update-ldif` action can be used to obtain the LDIF that updates the BDII information (for example the information about free/used space for a storage area). It's used, by default, by the scripts saved into /var/lib/bdii/gip/plugin directory, created launching the info provider script with configure.

### /usr/libexec/storm-info-provider get-report-json

The `get-report-json` action can be used to rebuild the WLCG JSON report. Administrators can change the output file by setting the command line option -o.

## OPTIONS

`-h`, `--help`:
    Print usage information.

`-v`=*LOG_LEVEL*:
    Set the logging level. Values: ‘10’ (DEBUG), ‘20’ (INFO), ‘30’ (WARNING) or ‘40’ (ERROR). Default value: ‘20’ (INFO).

`-o`=*LOG_FILENAME*:
    Redirect log messages to a file. LOG_FILENAME contains the file path.

### configure options:

`-f`=*FILEPATH*:
    Specify an alternative path to the file that contains the last StoRM related YAIM variables. Default value: `/etc/storm/info-provider/storm-yaim-variables.conf`.

`-g`=‘glue13|glue2|all’
    Specify the format of your published information: GLUE v1.3, GLUE v2 or both. Default value: ‘all’.

### get-static-ldif and get-update-ldif options:

`-f`=*FILEPATH*:
    Specify an alternative path to the file that contains the last StoRM related YAIM variables. Default value: `/etc/storm/info-provider/storm-yaim-variables.conf`.

`-g`=‘glue13|glue2’
    Specify the format of your published information: GLUE v1.3 or GLUE v2. Default value: ‘glue2’.

### get-report-json options:

`-f`=*FILEPATH*:
    Specify an alternative path to the file that contains the last StoRM related YAIM variables. Default value: `/etc/storm/info-provider/storm-yaim-variables.conf`.

`-o`=*FILEPATH*
    Specify an alternative path to the file that contains the generated JSON report. Default value: `/etc/storm/info-provider/site-report.json`.


## EXAMPLES

Examples of how the storm-info-provider script can be run.

### BDII integration

StoRM Info Provider provides the integration between StoRM storage service and resource BDII. 
This integration is initialized automatically by launching YAIM configuration. 
First of all, YAIM StoRM exports all the necessary variables into /etc/storm/info-provider/storm-yaim-variables.conf. 
Then, it launches the configure action like follow:

    /usr/libexec/storm-info-provider configure

As already said above, the default path for "-f" option is /etc/storm/info-provider/storm-yaim-variables.conf and the Glue version specified by "-g" is "all" by default (both Glue v1.3 and Glue v2).

To reconfigure only Glue v2 information:

    /usr/libexec/storm-info-provider configure -g glue2

To increase log verbosity:

    /usr/libexec/storm-info-provider -v 10 configure

To use another site info configuration file:

    /usr/libexec/storm-info-provider configure -f <your-site-info.conf>

To get the Glue v2 static information used by BDII run:

    /usr/libexec/storm-info-provider get-static-ldif

or

    /usr/libexec/storm-info-provider get-static-ldif -g glue13

for the Glue v1.3 format.

To get the current update information (Glue v2) of your StoRM storage service run:

    /usr/libexec/storm-info-provider get-update-ldif

or

    /usr/libexec/storm-info-provider get-update-ldif -g glue13

for the Glue v1.3 format.

The logging information of get-static-ldif and get-update-ldif actions are appended to BDII's log file: `/var/log/bdii/bdii-update.log`.

### WLCG JSON report generation

To export a JSON report of the storage service to `example.json`:

    /usr/libexec/storm-info-provider get-report-json -o example.json

## AUTHOR

Enrico Vianello <enrico.vianello@cnaf.infn.it>

## COPYRIGHT

Copyright (c) Members of the EGEE Collaboration. 2004. See the beneficiaries list for details on the copyright holders.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

www.apache.org/licenses/LICENSE-2.0: http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either  express  or  implied. See the License for the specific language governing permissions and limitations under the License.

## SEE ALSO
